# [FL_INDEX: keywords="blender_factory, procedural_3d, BedFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BedFactory | Category: factories_geo
# Prompt: A 3D model of a complete bed rendered from an elevated three-quarter perspective, featuring a wooden bed frame with a decorative headboard and footboard, tapered legs, a green mattress, layered bedding including a light pink blanket and a folded comforter with pillows arranged at the head.

# BedFactory — standalone Blender script (geometry + multi-material textures).
# BedFrame: wood/metal/plaster + wear_tear; Mattress/Sheet/Cover/Pillows: fabric.
import os
import bpy, bmesh, math
import random, colorsys
import numpy as np
from numpy.random import uniform
from mathutils import Vector

# Material library: wood, plaster, metals, plastic, wear_tear + fabric (raw bpy nodes)

def seed_all(seed: int):
    np.random.seed(seed)
    random.seed(seed)


def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)


def _mat_log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))


def metal_hsv():
    if np.random.uniform() < 0.2:
        return (np.random.uniform(0, 1),
                np.random.uniform(0.0, 0.2),
                _mat_log_uniform(0.05, 0.3))
    return (np.random.uniform(0, 1),
            np.random.uniform(0.3, 0.6),
            _mat_log_uniform(0.02, 0.5))


def bark_hsv():
    wood_hex = ["#8b5a2b", "#a0522d", "#cd853f", "#d2691e", "#6b4423", "#5d4037", "#7b3f00"]
    h_str = wood_hex[np.random.randint(0, len(wood_hex))].lstrip("#")
    r, g, b = (int(h_str[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return colorsys.rgb_to_hsv(r, g, b)


def weighted_sample_mat(reg):
    classes, weights = zip(*reg)
    weights = np.array(weights, dtype=float)
    return classes[int(np.random.choice(len(classes), p=weights / weights.sum()))]


def _new_material(name: str) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    return mat


def _set_principled(bsdf, **kw):
    """Set Principled BSDF inputs with Blender-version-tolerant socket names."""

    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Specular": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
        "Sheen Weight": ("Sheen Weight", "Sheen"),
    }
    for k, v in kw.items():
        names = aliases.get(k, (k,))
        for name in names:
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = v
                break


def _build_float_curve(nt, value_socket, anchors):
    fc = nt.nodes.new("ShaderNodeFloatCurve")
    fc.mapping.use_clip = False
    curve = fc.mapping.curves[0]
    for i, (x, y) in enumerate(anchors):
        if i < 2:
            curve.points[i].location = (x, y)
        else:
            curve.points.new(x, y)
        curve.points[i].handle_type = "VECTOR"
    fc.mapping.update()
    nt.links.new(value_socket, fc.inputs["Value"])
    return fc


def _noise_fac_output(noise_node):
    if "Fac" in noise_node.outputs:
        return noise_node.outputs["Fac"]
    if "Factor" in noise_node.outputs:
        return noise_node.outputs["Factor"]
    return noise_node.outputs[0]


def _connect_output(nt, bsdf, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    return out


# ----------------------------------------------------------------------------
# Material constructors
# ----------------------------------------------------------------------------
def make_brushed_metal(name="BrushedMetal", base_color_hsv=None) -> bpy.types.Material:
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    mapping_1.inputs["Scale"].default_value = (0.2, 0.2, 5.0)
    nt.links.new(tex_coord.outputs["Object"], mapping_1.inputs["Vector"])

    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise2, "noise_dimensions"):
        try: noise2.noise_dimensions = "4D"
        except TypeError: pass
    noise2.inputs["Scale"].default_value = 100.0
    if "Detail" in noise2.inputs:    noise2.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise2.inputs: noise2.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise2.inputs:noise2.inputs["Distortion"].default_value = 0.1
    if "W" in noise2.inputs:         noise2.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(mapping_1.outputs["Vector"], noise2.inputs["Vector"])

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[1].default_value = 0.4
    map_range.inputs[2].default_value = 0.6
    map_range.inputs[3].default_value = 0.8
    map_range.inputs[4].default_value = 1.2
    nt.links.new(_noise_fac_output(noise2), map_range.inputs[0])

    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Color"].default_value = hsv2rgba(base_color_hsv)
    nt.links.new(map_range.outputs["Result"], hsv_node.inputs["Value"])

    map_range_r = nt.nodes.new("ShaderNodeMapRange")
    map_range_r.inputs[1].default_value = 0.4
    map_range_r.inputs[2].default_value = 0.6
    map_range_r.inputs[3].default_value = 0.2
    map_range_r.inputs[4].default_value = 0.3
    nt.links.new(_noise_fac_output(noise2), map_range_r.inputs[0])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})
    nt.links.new(hsv_node.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(map_range_r.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat


def make_galvanized_metal(name="GalvanizedMetal", base_color_hsv=None) -> bpy.types.Material:
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(voronoi, "voronoi_dimensions"):
        try: voronoi.voronoi_dimensions = "4D"
        except TypeError: voronoi.voronoi_dimensions = "3D"
    if hasattr(voronoi, "distance"):
        try: voronoi.distance = "MINKOWSKI"
        except TypeError: pass
    voronoi.inputs["Scale"].default_value = 500.0
    if "W" in voronoi.inputs:
        voronoi.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], voronoi.inputs["Vector"])

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[3].default_value = 0.1
    map_range.inputs[4].default_value = 0.5
    nt.links.new(voronoi.outputs[0], map_range.inputs[0])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf, Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv)},
    )
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat


def make_grained_metal(name="GrainedMetal", base_color_hsv=None) -> bpy.types.Material:
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2000.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:          noise.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    roughness_input = float(np.random.uniform(0.0, 1.0))
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[0].default_value = roughness_input
    map_range.inputs[3].default_value = 0.05
    map_range.inputs[4].default_value = 0.25

    mul1 = nt.nodes.new("ShaderNodeMath")
    mul1.operation = "MULTIPLY"
    mul1.inputs[1].default_value = 0.4
    nt.links.new(map_range.outputs["Result"], mul1.inputs[0])
    mul2 = nt.nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    nt.links.new(_noise_fac_output(noise), mul2.inputs[0])
    nt.links.new(mul1.outputs[0], mul2.inputs[1])
    mul3 = nt.nodes.new("ShaderNodeMath")
    mul3.operation = "MULTIPLY"
    mul3.inputs[1].default_value = 0.01
    nt.links.new(mul2.outputs[0], mul3.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul3.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf, Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv)},
    )
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


def make_hammered_metal(name="HammeredMetal", base_color_hsv=None) -> bpy.types.Material:
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(voronoi, "feature"):
        try: voronoi.feature = "SMOOTH_F1"
        except TypeError: pass
    voronoi.inputs["Scale"].default_value = 300.0
    if "Smoothness" in voronoi.inputs:
        voronoi.inputs["Smoothness"].default_value = 0.2
    if "W" in voronoi.inputs:
        voronoi.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], voronoi.inputs["Vector"])

    pow_node = nt.nodes.new("ShaderNodeMath")
    pow_node.operation = "POWER"
    pow_node.inputs[1].default_value = 2.5
    dist_out = voronoi.outputs.get("Distance") or voronoi.outputs[0]
    nt.links.new(dist_out, pow_node.inputs[0])

    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = _mat_log_uniform(0.001, 0.003)
    nt.links.new(pow_node.outputs[0], mul.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf, Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv), "Roughness": 0.1},
    )
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


def make_plastic_rough(name="PlasticRough", base_color=None) -> bpy.types.Material:
    if base_color is None:
        base_color = hsv2rgba((np.random.uniform(0, 1),
                               np.random.uniform(0.5, 0.8),
                               _mat_log_uniform(0.01, 0.5)))
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2000.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:          noise.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    roughness_input = float(np.random.uniform(0.0, 1.0))
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[0].default_value = roughness_input
    map_range.inputs[3].default_value = 0.05
    map_range.inputs[4].default_value = 0.25

    mul1 = nt.nodes.new("ShaderNodeMath")
    mul1.operation = "MULTIPLY"
    mul1.inputs[1].default_value = 0.4
    nt.links.new(map_range.outputs["Result"], mul1.inputs[0])
    mul2 = nt.nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    nt.links.new(_noise_fac_output(noise), mul2.inputs[0])
    nt.links.new(mul1.outputs[0], mul2.inputs[1])
    mul3 = nt.nodes.new("ShaderNodeMath")
    mul3.operation = "MULTIPLY"
    mul3.inputs[1].default_value = 0.003
    nt.links.new(mul2.outputs[0], mul3.inputs[0])
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul3.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Base Color": base_color})
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


def make_wood(name="Wood", color=None) -> bpy.types.Material:
    if color is None:
        h, s, v = bark_hsv()
        # Mirror wood.py:get_color() hue/sat/value jitter
        color = hsv2rgba((h + np.random.uniform(-0.0, 0.05),
                          max(0.0, s + np.random.uniform(-0.3, 0.2)),
                          v * _mat_log_uniform(0.2, 20)))
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (5.0, 100.0, 100.0)
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    grain = nt.nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 10.0
    if "Detail" in grain.inputs:     grain.inputs["Detail"].default_value = 15.0
    if "Distortion" in grain.inputs: grain.inputs["Distortion"].default_value = 0.5
    nt.links.new(mapping.outputs["Vector"], grain.inputs["Vector"])

    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Saturation"].default_value = 0.8
    hsv_node.inputs["Value"].default_value = 0.2
    hsv_node.inputs["Color"].default_value = color

    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    nt.links.new(_noise_fac_output(grain), mix.inputs[0])
    nt.links.new(hsv_node.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = color

    # Low-frequency roughness variation (mirrors wood.py build_float_curve)
    noise_r = nt.nodes.new("ShaderNodeTexNoise")
    noise_r.inputs["Scale"].default_value = _mat_log_uniform(40, 50)
    base_rough = float(np.random.uniform(0.0, 0.4))
    fc = _build_float_curve(nt, _noise_fac_output(noise_r),
                            [(0, base_rough),
                             (1, base_rough + float(np.random.uniform(0.0, 0.8)))])

    # Tiny displacement from grain noise
    mul_disp = nt.nodes.new("ShaderNodeMath")
    mul_disp.operation = "MULTIPLY"
    mul_disp.inputs[1].default_value = _mat_log_uniform(0.0002, 0.01)
    nt.links.new(_noise_fac_output(grain), mul_disp.inputs[0])
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_disp.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf,
                    **{"Coat Weight": float(np.clip(np.random.uniform(0, 1.4), 0, 1))})
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


def make_plaster(name="Plaster", plaster_colored=None) -> bpy.types.Material:
    if plaster_colored is None:
        plaster_colored = np.random.uniform() < 0.4

    hue = float(np.random.uniform(0, 1))
    front_value = _mat_log_uniform(0.5, 1.0)
    back_value = front_value * float(np.random.uniform(0.6, 1.0))
    if plaster_colored:
        front_color = hsv2rgba((hue, float(np.random.uniform(0.3, 0.5)), front_value))
        back_color = hsv2rgba((hue + float(np.random.uniform(-0.1, 0.1)),
                               float(np.random.uniform(0.3, 0.5)), back_value))
    else:
        front_color = hsv2rgba((hue, 0.0, front_value))
        back_color = hsv2rgba((hue + float(np.random.uniform(-0.1, 0.1)), 0.0, back_value))

    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # Musgrave substitute: stretched NoiseTexture
    musgrave = nt.nodes.new("ShaderNodeTexNoise")
    if "Detail" in musgrave.inputs:
        musgrave.inputs["Detail"].default_value = _mat_log_uniform(15, 30)
    if "Roughness" in musgrave.inputs:
        musgrave.inputs["Roughness"].default_value = 0.5
    nt.links.new(tex_coord.outputs["Generated"], musgrave.inputs["Vector"])

    noise = nt.nodes.new("ShaderNodeTexNoise")
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = _mat_log_uniform(15, 30)
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = _mat_log_uniform(4, 8)
    nt.links.new(tex_coord.outputs["Generated"], noise.inputs["Vector"])

    # Noise through low->high color ramp
    cr_noise = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = cr_noise.inputs.get("Fac") or cr_noise.inputs[0]
    nt.links.new(_noise_fac_output(noise), fac_in)
    cr_noise.color_ramp.elements[0].position = 0.0
    cr_noise.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr_noise.color_ramp.elements[1].position = float(np.random.uniform(0.3, 0.5))
    cr_noise.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # Difference mix (musgrave vs noise ramp)
    diff = nt.nodes.new("ShaderNodeMix")
    if hasattr(diff, "data_type"):
        diff.data_type = "RGBA"
    if hasattr(diff, "blend_type"):
        try: diff.blend_type = "DIFFERENCE"
        except TypeError: pass
    diff.inputs[0].default_value = 1.0
    nt.links.new(_noise_fac_output(musgrave), diff.inputs[6])
    nt.links.new(cr_noise.outputs["Color"], diff.inputs[7])

    # Base color ramp (back -> front)
    cr_base = nt.nodes.new("ShaderNodeValToRGB")
    fac_in2 = cr_base.inputs.get("Fac") or cr_base.inputs[0]
    nt.links.new(diff.outputs[2], fac_in2)
    cr_base.color_ramp.elements[0].position = float(np.random.uniform(0.2, 0.3))
    cr_base.color_ramp.elements[0].color = back_color
    cr_base.color_ramp.elements[1].position = 1.0
    cr_base.color_ramp.elements[1].color = front_color

    # Displacement from high-frequency noise
    disp_noise = nt.nodes.new("ShaderNodeTexNoise")
    disp_noise.inputs["Scale"].default_value = float(np.random.uniform(1e3, 2e3))
    if "Detail" in disp_noise.inputs:
        disp_noise.inputs["Detail"].default_value = 5.0
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = _mat_log_uniform(0.0001, 0.0003)
    nt.links.new(_noise_fac_output(disp_noise), disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=float(np.random.uniform(0.7, 0.8)))
    nt.links.new(cr_base.outputs["Color"], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
FURNITURE_LEG = [
    (make_brushed_metal,    1.0),    # decorative_metal start
    (make_galvanized_metal, 1.0),
    (make_grained_metal,    1.0),
    (make_hammered_metal,   1.0),
    (make_wood,             1.0),
    # GlassVolume omitted (non-applicable to bedframe limbs visually)
    (make_plastic_rough,    1.0),
    (make_brushed_metal,    3.0),    # BrushedBlackMetal → approximated by brushed
    (make_wood,             3.0),    # BlackPlywood → wood variant
]

FURNITURE_HARD_SURFACE = [
    (make_plastic_rough, 1.0),
    (make_wood,          1.0),
]

DECORATIVE_METAL = [
    (make_brushed_metal,    1.0),
    (make_galvanized_metal, 1.0),
    (make_grained_metal,    1.0),
    (make_hammered_metal,   1.0),
]

BEDFRAME = DECORATIVE_METAL + [
    (make_wood,    7.0),
    (make_plaster, 2.0),
]

REGISTRY = {
    "bedframe": BEDFRAME,
    "furniture_hard_surface": FURNITURE_HARD_SURFACE,
    "furniture_leg": FURNITURE_LEG,
}


def get_material(registry_key: str, name: str = None) -> bpy.types.Material:
    ctor = weighted_sample_mat(REGISTRY[registry_key])
    return ctor(name=name or registry_key.title())


# ============================================================================
# wear_tear post-processing — faithful raw-bpy translation
# ============================================================================
WEAR_TEAR_PROB = [0.5, 0.5]
SCRATCH_LABEL = "scratch"
EDGE_WEAR_LABEL = "wear_tear"


def _find_node(nt, bl_idname):
    return next((n for n in nt.nodes if n.bl_idname == bl_idname), None)


def _math(nt, op, in0=None, in1=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    if in0 is not None:
        if hasattr(in0, "default_value") or hasattr(in0, "links"):
            nt.links.new(in0, n.inputs[0])
        else:
            n.inputs[0].default_value = in0
    if in1 is not None:
        if hasattr(in1, "default_value") or hasattr(in1, "links"):
            nt.links.new(in1, n.inputs[1])
        else:
            n.inputs[1].default_value = in1
    return n


def _vmath(nt, op, in0=None, in1=None, scale=None):
    n = nt.nodes.new("ShaderNodeVectorMath")
    n.operation = op
    if in0 is not None:
        if hasattr(in0, "links"):
            nt.links.new(in0, n.inputs[0])
        else:
            n.inputs[0].default_value = in0
    if in1 is not None:
        if hasattr(in1, "links"):
            nt.links.new(in1, n.inputs[1])
        else:
            n.inputs[1].default_value = in1
    if scale is not None:
        for inp in n.inputs:
            if inp.name == "Scale":
                inp.default_value = scale
                break
    return n


def _value_node(nt, value):
    n = nt.nodes.new("ShaderNodeValue")
    n.outputs[0].default_value = value
    return n


def _color_ramp(nt, fac_socket, stops):
    cr = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = cr.inputs.get("Fac") or cr.inputs[0]
    nt.links.new(fac_socket, fac_in)
    elements = cr.color_ramp.elements
    for i, (pos, color) in enumerate(stops):
        if i < len(elements):
            elements[i].position = pos
            elements[i].color = color
        else:
            e = elements.new(pos)
            e.color = color
    return cr


def _noise_tex(nt, vector_socket, scale, detail=2.0, distortion=0.0, roughness=0.5):
    n = nt.nodes.new("ShaderNodeTexNoise")
    if vector_socket is not None:
        nt.links.new(vector_socket, n.inputs["Vector"])
    if isinstance(scale, (int, float)):
        n.inputs["Scale"].default_value = float(scale)
    else:
        nt.links.new(scale, n.inputs["Scale"])
    if "Detail" in n.inputs:
        n.inputs["Detail"].default_value = detail
    if "Distortion" in n.inputs:
        n.inputs["Distortion"].default_value = distortion
    if "Roughness" in n.inputs:
        n.inputs["Roughness"].default_value = roughness
    return n


def get_scratch_params():
    return dict(
        angle1=float(np.random.uniform(10.0, 80.0)),
        angle2=float(np.random.uniform(-80.0, -10.0)),
        scratch_scale=_mat_log_uniform(5, 80),
        scratch_mask_ratio=_mat_log_uniform(0.01, 0.9),
        scratch_mask_noise=_mat_log_uniform(5, 40),
        scratch_depth=_mat_log_uniform(0.1, 1.0),
    )


def _build_scratch_graph(nt, params):
    n_angle1 = _value_node(nt, params["angle1"])
    n_angle2 = _value_node(nt, params["angle2"])
    n_scale = _value_node(nt, params["scratch_scale"])
    n_mask_ratio = _value_node(nt, params["scratch_mask_ratio"])
    n_mask_noise = _value_node(nt, params["scratch_mask_noise"])
    n_depth = _value_node(nt, params["scratch_depth"])

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    cxyz1 = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(n_angle1.outputs[0], cxyz1.inputs["Y"])
    map1 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map1, "vector_type"):
        try: map1.vector_type = "TEXTURE"
        except TypeError: pass
    map1.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map1.inputs["Vector"])
    nt.links.new(cxyz1.outputs[0], map1.inputs["Rotation"])
    noise1 = _noise_tex(nt, map1.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)

    cxyz2 = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(n_angle2.outputs[0], cxyz2.inputs["Y"])
    map2 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map2, "vector_type"):
        try: map2.vector_type = "TEXTURE"
        except TypeError: pass
    map2.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map2.inputs["Vector"])
    nt.links.new(cxyz2.outputs[0], map2.inputs["Rotation"])
    noise2 = _noise_tex(nt, map2.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)

    add = _math(nt, "ADD", _noise_fac_output(noise1), _noise_fac_output(noise2))

    map3 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map3, "vector_type"):
        try: map3.vector_type = "TEXTURE"
        except TypeError: pass
    map3.inputs["Rotation"].default_value = (0.1588, -0.5742, 0.1920)
    nt.links.new(tex_coord.outputs["Object"], map3.inputs["Vector"])
    noise3 = _noise_tex(nt, map3.outputs["Vector"], n_mask_noise.outputs[0], detail=1.0)
    cr_mask = _color_ramp(nt, _noise_fac_output(noise3),
                          [(0.4109, (0, 0, 0, 1)), (1.0, (1, 1, 1, 1))])
    mul_mask = _math(nt, "MULTIPLY", n_mask_ratio.outputs[0], cr_mask.outputs["Color"])
    add_combined = _math(nt, "ADD", add.outputs[0], mul_mask.outputs[0], clamp=True)

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[1].default_value = 0.7
    map_range.inputs[2].default_value = 0.72
    map_range.inputs[4].default_value = 0.9
    nt.links.new(add_combined.outputs[0], map_range.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(map_range.outputs["Result"], disp.inputs["Height"])
    nt.links.new(n_depth.outputs[0], disp.inputs["Scale"])

    return disp.outputs[0]


def apply_scratches(obj, **params):
    if obj is None or obj.data is None or not hasattr(obj.data, "materials"):
        return
    if not params:
        params = get_scratch_params()
    for slot_idx in range(len(obj.data.materials)):
        mat = obj.data.materials[slot_idx]
        if mat is None or not mat.use_nodes:
            continue
        nt = mat.node_tree
        if any(n.label == SCRATCH_LABEL for n in nt.nodes):
            continue
        mat_out = _find_node(nt, "ShaderNodeOutputMaterial")
        if mat_out is None:
            continue
        try:
            disp_out = _build_scratch_graph(nt, params)
            nt.links.new(disp_out, mat_out.inputs["Displacement"])
            disp_out.node.label = SCRATCH_LABEL
        except Exception as e:
            print(f"  [scratches] failed on {mat.name}: {type(e).__name__}: {e}")


def get_edge_wear_params():
    return dict(
        worn_off_opacity=float(np.random.uniform(0, 0.01)),
        worn_off_radius=float(np.random.uniform(0.005, 0.01)),
        scratch_radius=float(np.random.uniform(0.01, 0.03)),
        worn_off_mask_randomness=float(np.random.uniform(2.5, 3.0)),
        edge_base_color_hue=float(np.random.uniform(0.0, 1.0)),
        edge_base_color_whiteness=float(np.random.uniform(0.1, 0.6)),
        scratch_mask_randomness=float(np.random.choice(
            [np.random.uniform(0.1, 5.0), np.random.uniform(1.0, 10.0)])),
        scratch_density=float(np.random.uniform(1.5, 10.0)),
        scratch_opacity=float(np.random.uniform(0.5, 1.0)),
    )


def _build_edge_wear_graph(nt, original_bsdf_node, original_displacement_node, params):
    p = params
    n_scratch_opacity = _value_node(nt, p["scratch_opacity"])
    n_scratch_mask_randomness = _value_node(nt, p["scratch_mask_randomness"])
    n_scratch_radius = _value_node(nt, p["scratch_radius"])
    n_worn_opacity = _value_node(nt, p["worn_off_opacity"])
    n_worn_radius = _value_node(nt, p["worn_off_radius"])
    n_worn_mask_randomness = _value_node(nt, p["worn_off_mask_randomness"])
    n_edge_whiteness = _value_node(nt, p["edge_base_color_whiteness"])
    n_edge_hue = _value_node(nt, p["edge_base_color_hue"])
    n_scratch_density = _value_node(nt, p["scratch_density"])

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    noise_a = _noise_tex(nt, mapping.outputs["Vector"], n_scratch_mask_randomness.outputs[0], detail=1.0)
    cr_a = _color_ramp(nt, _noise_fac_output(noise_a),
                       [(0.4436, (0, 0, 0, 1)), (0.5345, (1, 1, 1, 1))])

    bevel = nt.nodes.new("ShaderNodeBevel")
    bevel.samples = 20
    nt.links.new(n_scratch_radius.outputs[0], bevel.inputs["Radius"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sub = _vmath(nt, "SUBTRACT", bevel.outputs[0], geo.outputs["Normal"])
    abs_a = _math(nt, "ABSOLUTE", sub.outputs["Vector"])
    cr_b = _color_ramp(nt, abs_a.outputs[0],
                       [(0.0691, (0, 0, 0, 1)), (0.1564, (1, 1, 1, 1))])

    mul_a = _math(nt, "MULTIPLY", cr_a.outputs["Color"], cr_b.outputs["Color"], clamp=True)
    mul_a1 = _math(nt, "MULTIPLY", n_scratch_opacity.outputs[0], mul_a.outputs[0], clamp=True)

    bevel2 = nt.nodes.new("ShaderNodeBevel")
    bevel2.samples = 20
    nt.links.new(n_worn_radius.outputs[0], bevel2.inputs["Radius"])
    sub2 = _vmath(nt, "SUBTRACT", bevel2.outputs[0], geo.outputs["Normal"])
    abs_b = _math(nt, "ABSOLUTE", sub2.outputs["Vector"])

    noise_b = _noise_tex(nt, mapping.outputs["Vector"], n_worn_mask_randomness.outputs[0], detail=1.0)
    cr_c = _color_ramp(nt, _noise_fac_output(noise_b),
                       [(0.0764, (1, 1, 1, 1)), (0.5709, (0, 0, 0, 1))])
    mul_b = _math(nt, "MULTIPLY", abs_b.outputs[0], cr_c.outputs["Color"], clamp=True)
    mul_b1 = _math(nt, "MULTIPLY", n_worn_opacity.outputs[0], mul_b.outputs[0], clamp=True)
    cr_d = _color_ramp(nt, mul_b1.outputs[0],
                       [(0.0, (0, 0, 0, 1)), (0.7782, (1, 1, 1, 1))])

    combine_color = nt.nodes.new("ShaderNodeCombineColor")
    if hasattr(combine_color, "mode"):
        try: combine_color.mode = "HSV"
        except TypeError: pass
    nt.links.new(n_edge_hue.outputs[0], combine_color.inputs["Red"])
    combine_color.inputs["Green"].default_value = 0.7733
    combine_color.inputs["Blue"].default_value = 0.0100

    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    if hasattr(mix, "clamp_result"):
        try: mix.clamp_result = True
        except TypeError: pass
    if hasattr(mix, "clamp_factor"):
        try: mix.clamp_factor = False
        except TypeError: pass
    nt.links.new(n_edge_whiteness.outputs[0], mix.inputs[0])
    nt.links.new(combine_color.outputs[0], mix.inputs[6])
    mix.inputs[7].default_value = (0.02, 0.02, 0.02, 1.0)

    bsdf_worn1 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix.outputs[2], bsdf_worn1.inputs["Base Color"])
    _set_principled(bsdf_worn1, Metallic=0.3745, Roughness=0.1436,
                    **{"Specular IOR Level": 0.0})

    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(cr_d.outputs["Color"], mix_shader.inputs["Fac"])
    nt.links.new(original_bsdf_node.outputs[0], mix_shader.inputs[1])
    nt.links.new(bsdf_worn1.outputs[0], mix_shader.inputs[2])

    map_h = nt.nodes.new("ShaderNodeMapping")
    map_h.inputs["Scale"].default_value = (10.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map_h.inputs["Vector"])
    vor_h = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(vor_h, "feature"):
        try: vor_h.feature = "DISTANCE_TO_EDGE"
        except TypeError: pass
    nt.links.new(map_h.outputs["Vector"], vor_h.inputs["Vector"])
    nt.links.new(n_scratch_density.outputs[0], vor_h.inputs["Scale"])

    map_v = nt.nodes.new("ShaderNodeMapping")
    map_v.inputs["Scale"].default_value = (1.0, 10.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map_v.inputs["Vector"])

    scale_v = _vmath(nt, "SCALE", in0=n_scratch_density.outputs[0], scale=2.0)
    vor_v = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(vor_v, "feature"):
        try: vor_v.feature = "DISTANCE_TO_EDGE"
        except TypeError: pass
    nt.links.new(map_v.outputs["Vector"], vor_v.inputs["Vector"])
    nt.links.new(scale_v.outputs[0], vor_v.inputs["Scale"])

    dist_h = vor_h.outputs.get("Distance") or vor_h.outputs[0]
    dist_v = vor_v.outputs.get("Distance") or vor_v.outputs[0]
    mul_dist = _math(nt, "MULTIPLY", dist_h, dist_v, clamp=True)
    cr_e = _color_ramp(nt, mul_dist.outputs[0],
                       [(0.0, (1, 1, 1, 1)), (0.0073, (0, 0, 0, 1))])
    mul_e = _math(nt, "MULTIPLY", cr_b.outputs["Color"], cr_e.outputs["Color"], clamp=True)
    mul_f = _math(nt, "MULTIPLY", mul_a.outputs[0], mul_e.outputs[0], clamp=True)

    bsdf_worn2 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix.outputs[2], bsdf_worn2.inputs["Base Color"])
    _set_principled(bsdf_worn2, Metallic=0.3855, Roughness=0.0,
                    **{"Specular IOR Level": 0.0})

    mix_shader_2 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mul_a1.outputs[0], mix_shader_2.inputs["Fac"])
    nt.links.new(mix_shader.outputs[0], mix_shader_2.inputs[1])
    nt.links.new(bsdf_worn2.outputs[0], mix_shader_2.inputs[2])

    scale_disp = _vmath(nt, "SCALE", in0=mul_f.outputs[0], scale=2.0)
    if original_displacement_node is None:
        total_displacement = scale_disp.outputs[0]
    else:
        add_disp = _math(nt, "ADD", original_displacement_node.outputs[0],
                         scale_disp.outputs[0], clamp=True)
        total_displacement = add_disp.outputs[0]

    return mix_shader_2.outputs[0], total_displacement


def apply_edge_wear(obj, **params):
    if obj is None or obj.data is None or not hasattr(obj.data, "materials"):
        return
    if not params:
        params = get_edge_wear_params()
    for slot_idx in range(len(obj.data.materials)):
        mat = obj.data.materials[slot_idx]
        if mat is None or not mat.use_nodes:
            continue
        nt = mat.node_tree
        if any(n.label == EDGE_WEAR_LABEL for n in nt.nodes):
            continue
        mat_out = _find_node(nt, "ShaderNodeOutputMaterial")
        if mat_out is None:
            continue
        surface_links = mat_out.inputs["Surface"].links
        if not surface_links:
            continue
        original_bsdf = surface_links[0].from_node
        disp_links = mat_out.inputs["Displacement"].links
        original_disp = disp_links[0].from_node if disp_links else None
        try:
            final_bsdf_socket, final_disp_socket = _build_edge_wear_graph(
                nt, original_bsdf, original_disp, params)
            nt.links.new(final_bsdf_socket, mat_out.inputs["Surface"])
            nt.links.new(final_disp_socket, mat_out.inputs["Displacement"])
            final_bsdf_socket.node.label = EDGE_WEAR_LABEL
        except Exception as e:
            print(f"  [edge_wear] failed on {mat.name}: {type(e).__name__}: {e}")


# ============================================================================
# === End of bedframe material library; fabric material helpers below =========
# ============================================================================

# Fabric-specific helpers (slightly different signatures from bedframe helpers above)
def _fab_log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _fab_weighted_sample(reg):
    classes, weights = zip(*reg)
    w = np.array(weights, dtype=float)
    return classes[int(np.random.choice(len(classes), p=w / w.sum()))]

def _fab_hsv2rgba(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(float(h) % 1.0, float(s), float(v))
    return (r, g, b, 1.0)

def mixture_of_gaussian(means, stds, weights, clamp_min=None, clamp_max=None):
    p = np.array(weights) / np.sum(weights)
    idx = int(np.random.choice(len(p), p=p))
    res = np.random.normal(means[idx], stds[idx])
    if clamp_min is not None: res = np.maximum(res, clamp_min)
    if clamp_max is not None: res = np.minimum(res, clamp_max)
    return res

def leather_hsv():
    return mixture_of_gaussian(
        means=np.array([[0.07, 0.45, 0.40], [0.6, 0.3, 0.40]]),
        stds=0.7 * np.array([[0.0035, 0.0063, 0.2], [0.0105, 0.028, 0.2]]),
        clamp_min=[0, 0, 0.06], clamp_max=[1, 1, 0.93], weights=[0.7, 0.3])

def fabric_hsv():
    return (float(np.random.uniform(0, 1)),
            float(np.random.uniform(0.3, 0.8)),
            float(np.random.uniform(0.6, 0.9)))

# Fabric node helpers (displacement takes a node; connect_out uses .outputs[0])
def _fab_fac(node):
    return node.outputs.get("Fac") or node.outputs.get("Factor") or node.outputs[0]

def _fab_connect_out(nt, surface, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(surface.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement.outputs[0], out.inputs["Displacement"])

def _fab_principled(nt, **kwargs):
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    for k, v in kwargs.items():
        nm = k.replace("_", " ")
        if nm in bsdf.inputs:
            bsdf.inputs[nm].default_value = v
        elif k == "Specular" and "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = v
    return bsdf


# ═══════════════════════════════════════════════════════════════════════════
#  Fabric shader constructors
#   code path as objects_blender_texture/clothes/ComforterFactory.py)
# ═══════════════════════════════════════════════════════════════════════════

def make_coarse_knit_fabric(name="CoarseKnitFabric"):
    pattern_mixer     = float(np.random.choice([np.random.uniform(0.0, 0.1),
                                                 np.random.uniform(0.1, 0.9)]))
    pattern_density   = float(np.random.choice([np.random.uniform(0.1, 1.0),
                                                 np.random.uniform(1.0, 10.0)]))
    color             = np.random.uniform(0.0, 1.0, 3)
    brick_knit        = float(np.random.choice([np.random.uniform(0.0, 0.05),
                                                 np.random.uniform(0.05, 0.95),
                                                 np.random.uniform(0.95, 1.0)]))
    knit_resolution   = float(np.random.uniform(0.5, 0.6))
    brick_resolution  = float(np.random.uniform(20.0, 30.0))
    crease_resolution = float(np.random.uniform(50.0, 80.0))
    smoothness        = float(np.random.choice([np.random.uniform(0.0, 0.2),
                                                 np.random.uniform(0.2, 0.5)]))
    color_shader_frac = float(np.random.uniform(0.1, 0.9))

    mat = _new_material(name); nt = mat.node_tree; ln = nt.links.new
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    map1 = nt.nodes.new("ShaderNodeMapping")
    ln(tex_coord.outputs["Object"], map1.inputs["Vector"])
    map1.inputs["Scale"].default_value = (3.2, 1.0, 1.0)

    brick = nt.nodes.new("ShaderNodeTexBrick")
    ln(map1.outputs["Vector"], brick.inputs["Vector"])
    brick.inputs["Scale"].default_value = brick_resolution

    cr1 = nt.nodes.new("ShaderNodeValToRGB")
    ln(brick.outputs["Color"], cr1.inputs["Fac"])
    cr1.color_ramp.elements[0].position = 0.0;  cr1.color_ramp.elements[0].color = (1, 1, 1, 1)
    cr1.color_ramp.elements[1].position = 1.0;  cr1.color_ramp.elements[1].color = (0, 0, 0, 1)

    map2 = nt.nodes.new("ShaderNodeMapping")
    ln(tex_coord.outputs["Object"], map2.inputs["Vector"])
    map2.inputs["Rotation"].default_value = (0, 0, 0.7854)
    map2.inputs["Scale"].default_value = (238.8, 1.0, 35.6)

    vor1 = nt.nodes.new("ShaderNodeTexVoronoi"); vor1.feature = "F2"
    ln(map2.outputs["Vector"], vor1.inputs["Vector"])
    vor1.inputs["Scale"].default_value = pattern_density
    vor1.inputs["Randomness"].default_value = 0.0

    cr2 = nt.nodes.new("ShaderNodeValToRGB")
    ln(vor1.outputs["Distance"], cr2.inputs["Fac"])
    cr2.color_ramp.elements[0].position = 0.1018; cr2.color_ramp.elements[0].color = (1, 1, 1, 1)
    cr2.color_ramp.elements[1].position = 1.0;    cr2.color_ramp.elements[1].color = (0, 0, 0, 1)

    mix_pat = nt.nodes.new("ShaderNodeMix")
    mix_pat.data_type = "RGBA"; mix_pat.clamp_result = True
    mix_pat.inputs[0].default_value = pattern_mixer
    ln(cr1.outputs["Color"], mix_pat.inputs[6])
    ln(cr2.outputs["Color"], mix_pat.inputs[7])

    bsdf1 = _fab_principled(nt, Specular=0.6309, Roughness=0.9945)
    ln(mix_pat.outputs[2], bsdf1.inputs["Base Color"])

    comb = nt.nodes.new("ShaderNodeCombineColor")
    comb.inputs["Red"].default_value   = float(color[0])
    comb.inputs["Green"].default_value = float(color[1])
    comb.inputs["Blue"].default_value  = float(color[2])
    bsdf2 = _fab_principled(nt, Specular=0.6309, Roughness=0.9945)
    ln(comb.outputs["Color"], bsdf2.inputs["Base Color"])

    msh = nt.nodes.new("ShaderNodeMixShader")
    msh.inputs["Fac"].default_value = color_shader_frac
    ln(bsdf1.outputs["BSDF"], msh.inputs[1]); ln(bsdf2.outputs["BSDF"], msh.inputs[2])

    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.use_clamp = True
    inv.inputs[0].default_value = 1.0; ln(cr1.outputs["Color"], inv.inputs[1])
    sc = nt.nodes.new("ShaderNodeMath"); sc.operation = "MULTIPLY"; sc.use_clamp = True
    ln(inv.outputs[0], sc.inputs[0]); sc.inputs[1].default_value = brick_knit

    map3 = nt.nodes.new("ShaderNodeMapping")
    ln(tex_coord.outputs["Object"], map3.inputs["Vector"])
    map3.inputs["Rotation"].default_value = (0, 0, 0.6196)
    map3.inputs["Scale"].default_value = (217.5, 176.2, 42.0)
    vor2 = nt.nodes.new("ShaderNodeTexVoronoi"); vor2.feature = "F2"
    ln(map3.outputs["Vector"], vor2.inputs["Vector"])
    vor2.inputs["Scale"].default_value = knit_resolution
    vor2.inputs["Randomness"].default_value = 0.0

    map4 = nt.nodes.new("ShaderNodeMapping")
    ln(tex_coord.outputs["Object"], map4.inputs["Vector"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    ln(map4.outputs["Vector"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = crease_resolution

    add_n = nt.nodes.new("ShaderNodeMath"); add_n.use_clamp = True
    ln(_fab_fac(noise), add_n.inputs[0]); add_n.inputs[1].default_value = smoothness
    mul_n = nt.nodes.new("ShaderNodeMath"); mul_n.operation = "MULTIPLY"; mul_n.use_clamp = True
    ln(vor2.outputs["Distance"], mul_n.inputs[0]); ln(add_n.outputs[0], mul_n.inputs[1])
    sub_n = nt.nodes.new("ShaderNodeMath"); sub_n.operation = "SUBTRACT"
    sub_n.inputs[0].default_value = 1.0; sub_n.inputs[1].default_value = brick_knit
    sc1 = nt.nodes.new("ShaderNodeMath"); sc1.operation = "MULTIPLY"
    ln(mul_n.outputs[0], sc1.inputs[0]); ln(sub_n.outputs[0], sc1.inputs[1])
    add1 = nt.nodes.new("ShaderNodeMath")
    ln(sc.outputs[0], add1.inputs[0]); ln(sc1.outputs[0], add1.inputs[1])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    ln(add1.outputs[0], disp.inputs["Height"])
    disp.inputs["Midlevel"].default_value = 0.4; disp.inputs["Scale"].default_value = 0.01
    _fab_connect_out(nt, msh, disp)
    return mat


def make_fine_knit_fabric(name="FineKnitFabric"):
    color              = np.random.uniform(0.2, 1.0, 3)
    roughness          = float(np.random.uniform(0, 1.0))
    thread_density_x   = float(np.random.uniform(100, 300))
    relative_density_y = float(np.random.uniform(0.75, 1.33))
    displacement_scale = float(np.random.uniform(0.001, 0.005))

    mat = _new_material(name); nt = mat.node_tree; ln = nt.links.new
    comb = nt.nodes.new("ShaderNodeCombineColor")
    comb.inputs["Red"].default_value   = float(color[0])
    comb.inputs["Green"].default_value = float(color[1])
    comb.inputs["Blue"].default_value  = float(color[2])
    bsdf1 = _fab_principled(nt, Roughness=roughness)
    ln(comb.outputs["Color"], bsdf1.inputs["Base Color"])

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    mul.inputs[0].default_value = thread_density_x; mul.inputs[1].default_value = relative_density_y

    wy = nt.nodes.new("ShaderNodeTexWave"); wy.bands_direction = "Y"
    ln(tex_coord.outputs["Object"], wy.inputs["Vector"])
    ln(mul.outputs[0], wy.inputs["Scale"])
    wy.inputs["Distortion"].default_value = 5.0; wy.inputs["Detail"].default_value = 6.1

    bsdf2 = _fab_principled(nt, Roughness=roughness)
    ln(wy.outputs["Color"], bsdf2.inputs["Base Color"])
    msh = nt.nodes.new("ShaderNodeMixShader"); msh.inputs["Fac"].default_value = 0.1333
    ln(bsdf1.outputs["BSDF"], msh.inputs[1]); ln(bsdf2.outputs["BSDF"], msh.inputs[2])

    wx = nt.nodes.new("ShaderNodeTexWave")
    ln(tex_coord.outputs["Object"], wx.inputs["Vector"])
    wx.inputs["Scale"].default_value = thread_density_x
    wx.inputs["Distortion"].default_value = 3.8; wx.inputs["Detail"].default_value = 6.1

    cr1 = nt.nodes.new("ShaderNodeValToRGB"); ln(wx.outputs["Color"], cr1.inputs["Fac"])
    cr1.color_ramp.elements[0].position = 0.8109; cr1.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr1.color_ramp.elements[1].position = 1.0;    cr1.color_ramp.elements[1].color = (1, 1, 1, 1)
    inv = nt.nodes.new("ShaderNodeInvert"); inv.inputs["Fac"].default_value = 0.84
    ln(cr1.outputs["Color"], inv.inputs["Color"])

    cr2 = nt.nodes.new("ShaderNodeValToRGB"); ln(wy.outputs["Color"], cr2.inputs["Fac"])
    cr2.color_ramp.elements[0].position = 0.0727; cr2.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr2.color_ramp.elements[1].position = 0.8655; cr2.color_ramp.elements[1].color = (1, 1, 1, 1)

    add = nt.nodes.new("ShaderNodeMath")
    ln(inv.outputs["Color"], add.inputs[0]); ln(cr2.outputs["Color"], add.inputs[1])
    disp = nt.nodes.new("ShaderNodeDisplacement")
    ln(add.outputs[0], disp.inputs["Height"])
    disp.inputs["Midlevel"].default_value = 0.4; disp.inputs["Scale"].default_value = displacement_scale
    _fab_connect_out(nt, msh, disp)
    return mat


def make_leather(name="Leather"):
    seed_val = float(np.random.uniform(-1000.0, 1000.0))
    scale = 1.0
    hsv = leather_hsv()
    base_color = _fab_hsv2rgba(float(hsv[0]), float(hsv[1]), float(hsv[2]))
    rough_lo = float(np.random.uniform(0.3, 0.5)); rough_hi = float(np.random.uniform(0.5, 0.7))

    mat = _new_material(name); nt = mat.node_tree; ln = nt.links.new
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    rgb = nt.nodes.new("ShaderNodeRGB"); rgb.outputs[0].default_value = base_color

    mul1 = nt.nodes.new("ShaderNodeMath"); mul1.operation = "MULTIPLY"
    mul1.inputs[0].default_value = scale; mul1.inputs[1].default_value = 10.0
    noise = nt.nodes.new("ShaderNodeTexNoise")
    try:
        noise.noise_dimensions = "4D"
    except Exception:
        noise.noise_dimensions = "3D"
    ln(tex_coord.outputs["Object"], noise.inputs["Vector"])
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = seed_val
    ln(mul1.outputs[0], noise.inputs["Scale"])
    noise.inputs["Detail"].default_value = 15.0; noise.inputs["Distortion"].default_value = 0.2

    cr = nt.nodes.new("ShaderNodeValToRGB"); ln(_fab_fac(noise), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.2841; cr.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr.color_ramp.elements[1].position = 0.9455; cr.color_ramp.elements[1].color = (1, 1, 1, 1)

    mix_ll = nt.nodes.new("ShaderNodeMix")
    mix_ll.data_type = "RGBA"; mix_ll.blend_type = "LINEAR_LIGHT"
    mix_ll.inputs[0].default_value = 0.02
    ln(tex_coord.outputs["Object"], mix_ll.inputs[6]); ln(noise.outputs["Color"], mix_ll.inputs[7])

    mul2 = nt.nodes.new("ShaderNodeMath"); mul2.operation = "MULTIPLY"
    mul2.inputs[0].default_value = scale; mul2.inputs[1].default_value = 800.0
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    try:
        vor.voronoi_dimensions = "4D"
    except Exception:
        vor.voronoi_dimensions = "3D"
    vor.feature = "DISTANCE_TO_EDGE"
    ln(mix_ll.outputs[2], vor.inputs["Vector"])
    if "W" in vor.inputs:
        vor.inputs["W"].default_value = seed_val
    ln(mul2.outputs[0], vor.inputs["Scale"])

    mul3 = nt.nodes.new("ShaderNodeMath"); mul3.operation = "MULTIPLY"; mul3.use_clamp = True
    ln(vor.outputs["Distance"], mul3.inputs[0]); mul3.inputs[1].default_value = scale

    hsv1 = nt.nodes.new("ShaderNodeHueSaturation"); hsv1.inputs["Value"].default_value = 0.6
    ln(rgb.outputs[0], hsv1.inputs["Color"])
    mix1 = nt.nodes.new("ShaderNodeMix"); mix1.data_type = "RGBA"
    ln(mul3.outputs[0], mix1.inputs[0])
    ln(rgb.outputs[0], mix1.inputs[6]); ln(hsv1.outputs["Color"], mix1.inputs[7])

    hsv2 = nt.nodes.new("ShaderNodeHueSaturation"); hsv2.inputs["Value"].default_value = 0.4
    ln(rgb.outputs[0], hsv2.inputs["Color"])
    mix2 = nt.nodes.new("ShaderNodeMix"); mix2.data_type = "RGBA"
    ln(cr.outputs["Color"], mix2.inputs[0])
    ln(mix1.outputs[2], mix2.inputs[6]); ln(hsv2.outputs["Color"], mix2.inputs[7])

    mr = nt.nodes.new("ShaderNodeMapRange"); ln(mix2.outputs[2], mr.inputs["Value"])
    mr.inputs[3].default_value = rough_lo; mr.inputs[4].default_value = rough_hi
    bsdf = _fab_principled(nt)
    ln(mix2.outputs[2], bsdf.inputs["Base Color"]); ln(mr.outputs[0], bsdf.inputs["Roughness"])

    m4 = nt.nodes.new("ShaderNodeMath"); m4.operation = "MULTIPLY"
    ln(mix1.outputs[2], m4.inputs[0]); m4.inputs[1].default_value = -0.2
    m5 = nt.nodes.new("ShaderNodeMath"); m5.operation = "MULTIPLY"
    ln(cr.outputs["Color"], m5.inputs[0]); m5.inputs[1].default_value = 0.05
    a = nt.nodes.new("ShaderNodeMath"); ln(m4.outputs[0], a.inputs[0]); ln(m5.outputs[0], a.inputs[1])
    m6 = nt.nodes.new("ShaderNodeMath"); m6.operation = "MULTIPLY"
    ln(a.outputs[0], m6.inputs[0]); m6.inputs[1].default_value = 0.02

    disp = nt.nodes.new("ShaderNodeDisplacement")
    ln(m6.outputs[0], disp.inputs["Height"]); disp.inputs["Midlevel"].default_value = 0.0
    _fab_connect_out(nt, bsdf, disp)
    return mat


def make_sofa_fabric(name="SofaFabric"):
    strength = _fab_log_uniform(0.005, 0.01)
    hsv = fabric_hsv(); rgba = _fab_hsv2rgba(*hsv)
    bright = float(np.random.uniform(-0.15, -0.05))

    mat = _new_material(name); nt = mat.node_tree; ln = nt.links.new
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    ln(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    rgb = nt.nodes.new("ShaderNodeRGB"); rgb.outputs[0].default_value = rgba
    bc = nt.nodes.new("ShaderNodeBrightContrast")
    ln(rgb.outputs[0], bc.inputs["Color"]); bc.inputs["Bright"].default_value = bright

    brick = nt.nodes.new("ShaderNodeTexBrick")
    ln(mapping.outputs["Vector"], brick.inputs["Vector"])
    ln(rgb.outputs[0], brick.inputs["Color1"]); ln(bc.outputs["Color"], brick.inputs["Color2"])
    brick.inputs["Scale"].default_value = 276.98
    brick.inputs["Mortar Size"].default_value = 0.01
    brick.inputs["Mortar Smooth"].default_value = 1.0
    brick.inputs["Bias"].default_value = 0.5; brick.inputs["Row Height"].default_value = 0.1
    brick.offset = 0.5479; brick.squash_frequency = 1

    bsdf = _fab_principled(nt, Roughness=0.8624)
    ln(brick.outputs["Color"], bsdf.inputs["Base Color"])
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = 1.0

    disp = nt.nodes.new("ShaderNodeDisplacement")
    ln(_fab_fac(brick), disp.inputs["Height"]); disp.inputs["Scale"].default_value = strength
    _fab_connect_out(nt, bsdf, disp)
    return mat


FABRICS_REGISTRY = [
    (make_coarse_knit_fabric, 1.0),
    (make_fine_knit_fabric,   1.0),
    (make_leather,            0.3),
    (make_sofa_fabric,        1.0),
]

def get_fabric_material(name="Fabric"):
    ctor = _fab_weighted_sample(FABRICS_REGISTRY)
    return ctor(name=name)


# Phase 1: material sampling under raw SEED (each sub-factory resets to SEED)
SEED = int(os.environ.get("SEED", "0"))

for _o in list(bpy.data.objects):
    bpy.data.objects.remove(_o, do_unlink=True)
for _m in list(bpy.data.meshes):
    bpy.data.meshes.remove(_m)
for _c in list(bpy.data.collections):
    if _c != bpy.context.scene.collection:
        bpy.data.collections.remove(_c)
for _ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(_ng)
for _cur in list(bpy.data.curves):
    bpy.data.curves.remove(_cur)
bpy.context.scene.cursor.location = (0, 0, 0)

# BedFrame material: consume RNG in bedframe.py __init__ order before sampling
seed_all(SEED)
_bf_width            = float(np.exp(np.random.uniform(np.log(1.4), np.log(2.4))))
_bf_size             = float(np.random.uniform(2, 2.4))
_bf_thickness        = float(np.random.uniform(0.05, 0.12))
_bf_has_all_legs     = (np.random.uniform() < 0.2)
_bf_leg_thickness    = float(np.random.uniform(0.08, 0.12))
_bf_leg_height       = float(np.random.uniform(0.2, 0.6))
# leg_decor_type via weighted_choice on (2,coiled)(2,pad)(1,plain)(2,legs)
_ldt_w  = np.array([2, 2, 1, 2], dtype=float)
_ldt_v  = ["coiled", "pad", "plain", "legs"]
_bf_leg_decor_type   = _ldt_v[int(np.random.choice(4, p=_ldt_w / _ldt_w.sum()))]
_bf_leg_decor_wrapped= (np.random.uniform() < 0.5)
_bf_back_height      = float(np.random.uniform(0.5, 1.3))
_bf_seat_subdiv_x    = int(np.random.randint(1, 4))
_bf_seat_subdiv_y    = int(np.exp(np.random.uniform(np.log(4), np.log(10))))
MAT_SURFACE = get_material("bedframe", "Surface")
MAT_LIMB    = get_material("furniture_hard_surface", "Limb")
MAT_PANEL   = MAT_SURFACE
_scratch_p, _edge_wear_p = WEAR_TEAR_PROB
WEAR_DO_SCRATCH  = (np.random.uniform() <= _scratch_p)
WEAR_DO_EDGEWEAR = (np.random.uniform() <= _edge_wear_p)

# Mattress material: consume mattress.py __init__ RNG order before sampling
seed_all(SEED)
_ = float(np.exp(np.random.uniform(np.log(0.9), np.log(2.0))))     # width
_ = float(np.random.uniform(2, 2.4))                               # size
_ = float(np.random.uniform(0.2, 0.35))                            # thickness
_ = float(np.exp(np.random.uniform(np.log(0.16), np.log(0.2))))    # dot_distance
_ = float(np.random.uniform(0.005, 0.02))                          # dot_size
_ = float(np.random.uniform(0.04, 0.08))                           # dot_depth
_mt_w = np.array([1, 1], dtype=float)
_ = ["coiled", "wrapped"][int(np.random.choice(2, p=_mt_w / _mt_w.sum()))]
MAT_MATTRESS = get_fabric_material("MattressFabric")

# Sheet/cover: BlanketFactory samples surface immediately after __init__
seed_all(SEED)
MAT_SHEET = get_fabric_material("SheetFabric")
seed_all(SEED)
MAT_COVER = get_fabric_material("CoverFabric")

# Pillow material: consume pillow.py __init__ RNG order before sampling
seed_all(SEED)
_ps_w = np.array([4, 4, 1, 1], dtype=float)
_ = ["square", "rectangle", "circle", "torus"][int(np.random.choice(4, p=_ps_w/_ps_w.sum()))]
_ = float(np.random.uniform(0.4, 0.7))
_ = float(np.exp(np.random.uniform(np.log(0.6), np.log(0.8))))
_ = float(np.random.uniform(0.02, 0.05))
_ = float(np.exp(np.random.uniform(np.log(0.006), np.log(0.008))))
if np.random.uniform() < 0.5:
    _ = float(np.exp(np.random.uniform(np.log(1), np.log(8))))
_ = (np.random.uniform() < 0.3)
_ = float(np.random.uniform(0.01, 0.02))
MAT_PILLOW = get_fabric_material("PillowFabric")

# Reset to SEED for geometry block
random.seed(SEED); np.random.seed(SEED)


def log_uniform(lo, hi, size=None):
    if size is not None:
        return np.exp(uniform(np.log(lo), np.log(hi), size))
    return float(np.exp(uniform(np.log(lo), np.log(hi))))

def weighted_choice(choices):
    """choices = list of (weight, value)"""

    weights = [c[0] for c in choices]
    values = [c[1] for c in choices]
    total = sum(weights)
    r = random.random() * total
    cur = 0
    for w, v in zip(weights, values):
        cur += w
        if r <= cur:
            return v
    return values[-1]

# ── Blender utility wrappers ──

class ViewportMode:
    """Context manager to switch object mode and restore on exit."""

    def __init__(self, obj, mode):
        self.obj = obj
        self.mode = mode
    def __enter__(self):
        self.orig_active = bpy.context.active_object
        bpy.context.view_layer.objects.active = self.obj
        self.orig_mode = bpy.context.object.mode
        bpy.ops.object.mode_set(mode=self.mode)
    def __exit__(self, *args):
        bpy.context.view_layer.objects.active = self.obj
        bpy.ops.object.mode_set(mode=self.orig_mode)
        bpy.context.view_layer.objects.active = self.orig_active

def select_none():
    if hasattr(bpy.context, 'active_object') and bpy.context.active_object is not None:
        bpy.context.active_object.select_set(False)
    if hasattr(bpy.context, 'selected_objects'):
        for obj in bpy.context.selected_objects:
            obj.select_set(False)

def select_obj(obj):
    select_none()
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

def apply_transform(obj, loc=False, rot=True, scale=True):
    select_obj(obj)
    bpy.ops.object.transform_apply(location=loc, rotation=rot, scale=scale)

def apply_modifiers(obj, mod=None):
    if mod is None:
        mod = list(obj.modifiers)
    if not isinstance(mod, list):
        mod = [mod]
    for i, v in enumerate(mod):
        if isinstance(v, str):
            mod[i] = obj.modifiers[v]
    select_obj(obj)
    for m in mod:
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except RuntimeError:
            try:
                bpy.ops.object.modifier_remove(modifier=m.name)
            except RuntimeError:
                pass

def modify_mesh(obj, mod_type, apply=True, **kwargs):
    mod = obj.modifiers.new(name=f"mod_{mod_type}", type=mod_type)
    mod.show_viewport = not apply
    for k, v in kwargs.items():
        setattr(mod, k, v)
    if apply:
        apply_modifiers(obj, mod=mod)
    return obj

def deep_clone_obj(obj):
    new_obj = obj.copy()
    new_obj.data = obj.data.copy()
    for mod in list(new_obj.modifiers):
        new_obj.modifiers.remove(mod)
    while len(new_obj.data.materials) > 0:
        new_obj.data.materials.pop()
    bpy.context.scene.collection.objects.link(new_obj)
    return new_obj

def join_objects(objs):
    select_none()
    if not isinstance(objs, list):
        objs = [objs]
    if len(objs) == 0:
        return None
    if len(objs) == 1:
        return objs[0]
    bpy.context.view_layer.objects.active = objs[0]
    select_none()
    for o in objs:
        o.select_set(True)
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.location = (0, 0, 0)
    obj.rotation_euler = (0, 0, 0)
    obj.scale = (1, 1, 1)
    select_none()
    return obj

def subsurf(obj, levels):
    if levels > 0:
        modify_mesh(obj, 'SUBSURF', levels=levels, render_levels=levels)

# ── Mesh data utilities ──

def read_co(obj):
    arr = np.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get('co', arr)
    return arr.reshape(-1, 3)

def write_co(obj, arr):
    obj.data.vertices.foreach_set('co', arr.reshape(-1))

def read_edges(obj):
    arr = np.zeros(len(obj.data.edges) * 2, dtype=int)
    obj.data.edges.foreach_get('vertices', arr)
    return arr.reshape(-1, 2)

def read_edge_center(obj):
    return read_co(obj)[read_edges(obj).reshape(-1)].reshape(-1, 2, 3).mean(1)

def _normalize(v):
    n = np.linalg.norm(v, axis=-1)
    res = np.copy(v)
    mask = n > 0
    res[mask] /= n[mask, None]
    return res

def read_edge_direction(obj):
    cos = read_co(obj)[read_edges(obj).reshape(-1)].reshape(-1, 2, 3)
    return _normalize(cos[:, 1] - cos[:, 0])

def read_normal(obj):
    arr = np.zeros(len(obj.data.polygons) * 3)
    obj.data.polygons.foreach_get('normal', arr)
    return arr.reshape(-1, 3)

def read_center(obj):
    arr = np.zeros(len(obj.data.polygons) * 3)
    obj.data.polygons.foreach_get('center', arr)
    return arr.reshape(-1, 3)

# ── Mesh operations ──

def new_grid(x_subdivisions=1, y_subdivisions=1):
    bpy.ops.mesh.primitive_grid_add(
        location=(0, 0, 0),
        x_subdivisions=x_subdivisions,
        y_subdivisions=y_subdivisions
    )
    obj = bpy.context.active_object
    apply_transform(obj, loc=True)
    return obj

def remove_faces(obj, to_delete):
    to_delete = np.nonzero(to_delete)[0]
    with ViewportMode(obj, 'EDIT'):
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        geom = [bm.faces[i] for i in to_delete]
        bmesh.ops.delete(bm, geom=geom, context='FACES_ONLY')
        bmesh.update_edit_mesh(obj.data)
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_loose()
        bpy.ops.mesh.delete(type='EDGE')
    return obj

def remove_edges(obj, to_delete):
    to_delete = np.nonzero(to_delete)[0]
    with ViewportMode(obj, 'EDIT'):
        bm = bmesh.from_edit_mesh(obj.data)
        bm.edges.ensure_lookup_table()
        geom = [bm.edges[i] for i in to_delete]
        bmesh.ops.delete(bm, geom=geom, context='EDGES_FACES')
        bmesh.update_edit_mesh(obj.data)
    return obj

def remove_vertices(obj, to_delete_fn):
    x, y, z = read_co(obj).T
    to_delete = to_delete_fn(x, y, z)
    to_delete = np.nonzero(to_delete)[0]
    with ViewportMode(obj, 'EDIT'):
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        geom = [bm.verts[i] for i in to_delete]
        bmesh.ops.delete(bm, geom=geom)
        bmesh.update_edit_mesh(obj.data)
    return obj

def select_edges(obj, to_select):
    to_select = np.nonzero(to_select)[0]
    with ViewportMode(obj, 'EDIT'):
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(obj.data)
        bm.edges.ensure_lookup_table()
        for i in to_select:
            bm.edges[i].select_set(True)
        bm.select_flush(False)
        bmesh.update_edit_mesh(obj.data)
    return obj

def select_faces(obj, to_select):
    to_select = np.nonzero(to_select)[0]
    with ViewportMode(obj, 'EDIT'):
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        for i in to_select:
            bm.faces[i].select_set(True)
        bm.select_flush(False)
        bmesh.update_edit_mesh(obj.data)
    return obj

def subdivide_edge_ring(obj, cuts=64, axis=(0, 0, 1)):
    select_none()
    with ViewportMode(obj, 'EDIT'):
        bm = bmesh.from_edit_mesh(obj.data)
        bm.edges.ensure_lookup_table()
        selected = (
            np.abs((read_edge_direction(obj) * np.array(axis)[np.newaxis, :]).sum(1))
            > 1 - 1e-3
        )
        edges = [bm.edges[i] for i in np.nonzero(selected)[0]]
        bmesh.ops.subdivide_edgering(bm, edges=edges, cuts=int(cuts))
        bmesh.update_edit_mesh(obj.data)

def solidify_cross_section(obj, axis, thickness):
    """Extrude edges along two perpendicular axes to create rectangular cross-section."""

    axes = [0, 1, 2]
    axes.remove(axis)
    u = np.zeros(3)
    u[axes[0]] = thickness
    v = np.zeros(3)
    v[axes[1]] = thickness
    select_none()
    with ViewportMode(obj, 'EDIT'):
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.extrude_edges_move(TRANSFORM_OT_translate={'value': tuple(u)})
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={'value': tuple(v)})
    obj.location = -(u + v) / 2
    apply_transform(obj, loc=True)
    return obj

def dissolve_limited(obj):
    with ViewportMode(obj, 'EDIT'):
        for angle_limit in reversed(0.05 * 0.1 ** np.arange(5)):
            bpy.ops.mesh.select_mode(type='FACE')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.dissolve_limited(angle_limit=angle_limit)

def write_attr_data(obj, name, data, type_str='FLOAT', domain='FACE'):
    if name in obj.data.attributes:
        attr = obj.data.attributes[name]
    else:
        attr = obj.data.attributes.new(name, type_str, domain)
    FIELDS = {
        'FLOAT': 'value', 'INT': 'value', 'FLOAT_VECTOR': 'vector',
        'FLOAT_COLOR': 'color', 'BYTE_COLOR': 'color', 'BOOLEAN': 'value',
        'FLOAT2': 'vector', 'INT8': 'value', 'INT32_2D': 'value',
        'QUATERNION': 'value',
    }
    field = FIELDS.get(attr.data_type, 'value')
    attr.data.foreach_set(field, np.asarray(data).reshape(-1))

def set_active_attribute(obj, name):
    attributes = obj.data.attributes
    for i, a in enumerate(attributes):
        if a.name == name:
            attributes.active_index = i
            attributes.active = attributes[i]
            break

# ── Bezier curve utilities ──

def bezier_curve(anchors, vector_locations=(), resolution=None, to_mesh=True):
    n = anchors.shape[1] if anchors.ndim == 2 else len(anchors[0])
    if anchors.ndim == 1:
        anchors = np.array(anchors)
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
    obj = bpy.context.active_object

    if n > 2:
        with ViewportMode(obj, 'EDIT'):
            bpy.ops.curve.subdivide(number_cuts=n - 2)
    points = obj.data.splines[0].bezier_points
    for i in range(n):
        points[i].co = (anchors[0, i], anchors[1, i], anchors[2, i])
    for i in range(n):
        if i in vector_locations:
            points[i].handle_left_type = 'VECTOR'
            points[i].handle_right_type = 'VECTOR'
        else:
            points[i].handle_left_type = 'AUTO'
            points[i].handle_right_type = 'AUTO'
    obj.data.splines[0].resolution_u = resolution if resolution is not None else 12
    if not to_mesh:
        return obj
    return curve2mesh(obj)

def curve2mesh(obj):
    points = obj.data.splines[0].bezier_points
    cos = np.array([p.co for p in points])
    length = np.linalg.norm(cos[:-1] - cos[1:], axis=-1)
    min_length = 5e-3
    with ViewportMode(obj, 'EDIT'):
        for i in range(len(points)):
            if points[i].handle_left_type == 'FREE':
                points[i].handle_left_type = 'ALIGNED'
            if points[i].handle_right_type == 'FREE':
                points[i].handle_right_type = 'ALIGNED'
        for i in reversed(range(len(points) - 1)):
            points = list(obj.data.splines[0].bezier_points)
            number_cuts = min(int(length[i] / min_length) - 1, 64)
            if number_cuts < 0:
                continue
            bpy.ops.curve.select_all(action='DESELECT')
            points[i].select_control_point = True
            points[i + 1].select_control_point = True
            bpy.ops.curve.subdivide(number_cuts=number_cuts)
    obj.data.splines[0].resolution_u = 1
    select_obj(obj)
    bpy.ops.object.convert(target='MESH')
    obj = bpy.context.active_object
    modify_mesh(obj, 'WELD', merge_threshold=1e-3)
    return obj

def align_bezier(anchors, axes=None, scale=None, vector_locations=(), resolution=None, to_mesh=True):
    obj = bezier_curve(anchors, vector_locations, resolution, False)
    points = obj.data.splines[0].bezier_points
    n_pts = len(points)
    if scale is None:
        scale = np.ones(2 * n_pts - 2)
    if axes is None:
        axes = [None] * n_pts
    scale = [1, *scale, 1]
    for i, p in enumerate(points):
        a = axes[i]
        if a is None:
            continue
        a = np.array(a, dtype=float)
        p.handle_left_type = 'FREE'
        p.handle_right_type = 'FREE'
        proj_left = np.array(p.handle_left - p.co) @ a * a
        norm_pl = np.linalg.norm(proj_left)
        if norm_pl > 1e-8:
            p.handle_left = (
                np.array(p.co) + proj_left / norm_pl
                * np.linalg.norm(np.array(p.handle_left) - np.array(p.co)) * scale[2 * i]
            )
        proj_right = np.array(p.handle_right - p.co) @ a * a
        norm_pr = np.linalg.norm(proj_right)
        if norm_pr > 1e-8:
            p.handle_right = (
                np.array(p.co) + proj_right / norm_pr
                * np.linalg.norm(np.array(p.handle_right) - np.array(p.co)) * scale[2 * i + 1]
            )
    if not to_mesh:
        return obj
    return curve2mesh(obj)

# ── GeoNodes: geo_radius ──

def create_geo_radius_nodegroup(radius, resolution=6, merge_distance=0.004):
    ng = bpy.data.node_groups.new("geo_radius", 'GeometryNodeTree')
    in_sock = ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    out_sock = ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.move(in_sock, 0)

    group_in = ng.nodes.new('NodeGroupInput')
    group_in.location = (-600, 0)
    group_out = ng.nodes.new('NodeGroupOutput')
    group_out.location = (600, 0)

    mesh2curve = ng.nodes.new('GeometryNodeMeshToCurve')
    mesh2curve.location = (-400, 0)
    ng.links.new(group_in.outputs['Geometry'], mesh2curve.inputs['Mesh'])

    set_radius = ng.nodes.new('GeometryNodeSetCurveRadius')
    set_radius.location = (-200, 0)
    ng.links.new(mesh2curve.outputs['Curve'], set_radius.inputs['Curve'])
    set_radius.inputs['Radius'].default_value = radius

    curve_circle = ng.nodes.new('GeometryNodeCurvePrimitiveCircle')
    curve_circle.location = (-200, -200)
    curve_circle.mode = 'RADIUS'
    curve_circle.inputs['Resolution'].default_value = resolution
    curve_circle.inputs['Radius'].default_value = radius  # Blender 5.0: CurveToMesh ignores SetCurveRadius

    curve2mesh_node = ng.nodes.new('GeometryNodeCurveToMesh')
    curve2mesh_node.location = (0, 0)
    ng.links.new(set_radius.outputs['Curve'], curve2mesh_node.inputs['Curve'])
    ng.links.new(curve_circle.outputs['Curve'], curve2mesh_node.inputs['Profile Curve'])
    for inp in curve2mesh_node.inputs:
        if inp.name == 'Fill Caps':
            inp.default_value = True

    if merge_distance > 0:
        merge = ng.nodes.new('GeometryNodeMergeByDistance')
        merge.location = (200, 0)
        ng.links.new(curve2mesh_node.outputs['Mesh'], merge.inputs['Geometry'])
        merge.inputs['Distance'].default_value = merge_distance
        ng.links.new(merge.outputs['Geometry'], group_out.inputs['Geometry'])
    else:
        ng.links.new(curve2mesh_node.outputs['Mesh'], group_out.inputs['Geometry'])

    return ng

def apply_geo_radius(obj, radius, resolution=32, merge_distance=0.004):
    ng = create_geo_radius_nodegroup(radius, resolution, merge_distance)
    mod = obj.modifiers.new("geo_radius", 'NODES')
    mod.node_group = ng
    apply_modifiers(obj, mod=mod)
    bpy.data.node_groups.remove(ng)
    return obj

# ── GeoNodes: scale elements (for make_coiled) ──

def create_scale_elements_nodegroup(scale_val):
    ng = bpy.data.node_groups.new("geo_scale", 'GeometryNodeTree')
    in_sock = ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    out_sock = ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.move(in_sock, 0)

    group_in = ng.nodes.new('NodeGroupInput')
    group_in.location = (-400, 0)
    group_out = ng.nodes.new('NodeGroupOutput')
    group_out.location = (400, 0)

    named_attr = ng.nodes.new('GeometryNodeInputNamedAttribute')
    named_attr.location = (-200, -100)
    named_attr.data_type = 'FLOAT'
    named_attr.inputs['Name'].default_value = 'tip'

    scale_elem = ng.nodes.new('GeometryNodeScaleElements')
    scale_elem.location = (0, 0)
    ng.links.new(group_in.outputs['Geometry'], scale_elem.inputs['Geometry'])
    ng.links.new(named_attr.outputs['Attribute'], scale_elem.inputs['Selection'])
    scale_elem.inputs['Scale'].default_value = scale_val

    ng.links.new(scale_elem.outputs['Geometry'], group_out.inputs['Geometry'])
    return ng

def apply_scale_elements(obj, scale_val):
    ng = create_scale_elements_nodegroup(scale_val)
    mod = obj.modifiers.new("geo_scale", 'NODES')
    mod.node_group = ng
    apply_modifiers(obj, mod=mod)
    bpy.data.node_groups.remove(ng)

# ── make_coiled ──

def make_coiled(obj, dot_distance, dot_depth, dot_size):
    with ViewportMode(obj, 'EDIT'):
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.poke()
        bpy.ops.mesh.tris_convert_to_quads()
        bpy.ops.mesh.poke()
        bpy.ops.mesh.poke()
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(obj.data)
        for v in bm.verts:
            if len(v.link_edges) == 16:
                v.select_set(True)
        bm.select_flush(False)
        bmesh.update_edit_mesh(obj.data)
        radius = dot_distance * uniform(0.06, 0.08)
        bpy.ops.mesh.bevel(offset=radius, affect='VERTICES')
        bpy.ops.mesh.extrude_region_shrink_fatten(
            TRANSFORM_OT_shrink_fatten={'value': -dot_depth}
        )
        bpy.ops.mesh.extrude_region_shrink_fatten(
            TRANSFORM_OT_shrink_fatten={'value': dot_depth}
        )
        bpy.ops.mesh.select_more()
        bpy.ops.mesh.select_more()

    write_attr_data(obj, 'tip', np.zeros(len(obj.data.polygons)), 'FLOAT', 'FACE')

    with ViewportMode(obj, 'EDIT'):
        set_active_attribute(obj, 'tip')
        bpy.ops.mesh.attribute_set(value_float=1)

    scale_val = dot_size / radius if radius > 1e-6 else 1.0
    apply_scale_elements(obj, scale_val)

    modify_mesh(obj, 'TRIANGULATE', min_vertices=4)
    modify_mesh(obj, 'SMOOTH', factor=uniform(0.5, 1.0), iterations=5)

# ── Cloth simulation ──

def cloth_sim(obj, collision_objs=None, end_frame=50, **kwargs):
    """Run cloth simulation, bake, apply, then remove collision modifiers."""

    if collision_objs is not None:
        if not isinstance(collision_objs, list):
            collision_objs = [collision_objs]
        for o in collision_objs:
            o.modifiers.new("Collision", 'COLLISION')
            o.collision.damping_factor = 0.9
            o.collision.cloth_friction = 10.0
            o.collision.friction_factor = 1.0
            o.collision.stickiness = 0.9
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    mod = obj.modifiers.new("Cloth", 'CLOTH')
    mod.settings.effector_weights.gravity = kwargs.pop('gravity', 1)
    mod.collision_settings.distance_min = kwargs.pop('distance_min', 0.015)
    mod.collision_settings.use_self_collision = kwargs.pop('use_self_collision', False)
    for k, v in kwargs.items():
        setattr(mod.settings, k, v)
    mod.point_cache.frame_start = 1
    mod.point_cache.frame_end = end_frame
    override = {'scene': bpy.context.scene, 'active_object': obj, 'point_cache': mod.point_cache}
    with bpy.context.temp_override(**override):
        bpy.ops.ptcache.bake(bake=True)
    bpy.context.scene.frame_set(end_frame)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.select_set(False)
    if collision_objs is not None:
        for o in collision_objs:
            bpy.context.view_layer.objects.active = o
            o.select_set(True)
            # Remove last modifier (should be Collision)
            if len(o.modifiers) > 0:
                bpy.ops.object.modifier_remove(modifier=o.modifiers[-1].name)
            o.select_set(False)
    # Reset frame for next simulation
    bpy.context.scene.frame_set(0)

# ═══════════════════════════════════════════════════════════════════
#  BedFrameFactory (inlined from BedFrameFactory.py)
# ═══════════════════════════════════════════════════════════════════

class BedFrameFactory:
    def __init__(self, seed):
        np.random.seed(seed)
        random.seed(seed)

        self.width = log_uniform(1.4, 2.4)
        self.size = uniform(2, 2.4)
        self.thickness = uniform(0.05, 0.12)
        self.bevel_width = self.thickness * (0.1 if uniform() < 0.4 else 0.5)

        self.has_all_legs = uniform() < 0.2
        self.leg_thickness = uniform(0.08, 0.12)
        self.leg_height = uniform(0.2, 0.6)

        self.leg_decor_type = weighted_choice(
            [(2, "coiled"), (2, "pad"), (1, "plain"), (2, "legs")]
        )
        self.leg_decor_wrapped = uniform() < 0.5

        self.back_height = uniform(0.5, 1.3)
        self.seat_back = 1
        self.seat_subdivisions_x = np.random.randint(1, 4)
        self.seat_subdivisions_y = int(log_uniform(4, 10))
        self.has_arm = False
        self.leg_type = "vertical"
        self.leg_x_offset = 0
        self.leg_y_offset = (0, 0)
        self.back_x_offset = 0
        self.back_y_offset = 0

        self.is_leg_round = uniform() < 0.5
        self.limb_profile = uniform(1.5, 2.5)
        self.back_thickness = uniform(0.04, 0.05)

        self.back_type = weighted_choice(
            [(3, "coiled"), (3, "pad"), (2, "whole"), (1, "horizontal-bar"), (1, "vertical-bar")]
        )
        self.back_profile = [(0, 1)]
        self.back_vertical_cuts = np.random.randint(1, 4)
        self.back_partial_scale = uniform(1, 1.4)

        self.dot_distance = log_uniform(0.16, 0.2)
        self.dot_size = uniform(0.005, 0.02)
        self.dot_depth = uniform(0.04, 0.08)
        self.panel_distance = uniform(0.3, 0.5)
        self.panel_margin = uniform(0.01, 0.02)

        self.has_leg_x_bar = uniform() < 0.6
        self.has_leg_y_bar = uniform() < 0.6
        self.leg_offset_bar = (uniform(0.2, 0.4), uniform(0.6, 0.8))

        self.post_init()

    def post_init(self):
        match self.back_type:
            case "partial":
                self.back_profile = ((uniform(0.4, 0.8), 1),)
            case "horizontal-bar":
                n_cuts = np.random.randint(2, 4)
                locs = uniform(1, 2, n_cuts).cumsum()
                locs = locs / locs[-1]
                ratio = uniform(0.5, 0.75)
                locs = np.array([
                    (p + ratio * (l - p), l)
                    for p, l in zip([0, *locs[:-1]], locs)
                ])
                lowest = uniform(0, 0.4)
                self.back_profile = locs * (1 - lowest) + lowest
            case "vertical-bar":
                self.back_profile = ((uniform(0.8, 0.9), 1),)
            case _:
                self.back_profile = [(0, 1)]

    # ── Seat ──
    def make_seat(self):
        obj = new_grid(
            x_subdivisions=self.seat_subdivisions_x,
            y_subdivisions=self.seat_subdivisions_y,
        )
        obj.scale = (
            (self.width - self.leg_thickness) / 2,
            (self.size - self.leg_thickness) / 2,
            1,
        )
        apply_transform(obj, True)
        with ViewportMode(obj, 'EDIT'):
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.delete(type='ONLY_FACE')
            bpy.ops.mesh.select_mode(type='EDGE')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.extrude_edges_move(
                TRANSFORM_OT_translate={'value': (0, 0, self.thickness)}
            )
        modify_mesh(
            obj, 'SOLIDIFY',
            thickness=self.leg_thickness - 1e-3,
            offset=0,
            solidify_mode='NON_MANIFOLD',
        )
        obj.location = (0, -self.size / 2, -self.thickness / 2)
        apply_transform(obj, loc=True)
        modify_mesh(obj, 'BEVEL', width=self.bevel_width, segments=8)
        return obj

    # ── Legs ──
    def make_legs(self):
        leg_starts = np.array([
            [-1, 0, 0], [-1, -1, 0], [1, -1, 0], [1, 0, 0]
        ]) * np.array([[self.width / 2, self.size, 0]])
        leg_ends = leg_starts.copy()
        leg_ends[[0, 1], 0] -= self.leg_x_offset
        leg_ends[[2, 3], 0] += self.leg_x_offset
        leg_ends[[0, 3], 1] += self.leg_y_offset[0]
        leg_ends[[1, 2], 1] -= self.leg_y_offset[1]
        leg_ends[:, -1] = -self.leg_height
        legs = self.make_limb(leg_ends, leg_starts)

        if self.has_all_legs:
            mid_starts = np.array([
                [-1, -0.5, 0], [0, -1, 0], [0, 0, 0], [1, -0.5, 0]
            ]) * np.array([[self.width / 2, self.size, 0]])
            mid_ends = mid_starts.copy()
            mid_ends[0, 0] -= self.leg_x_offset
            mid_ends[3, 0] += self.leg_x_offset
            mid_ends[2, 1] += self.leg_y_offset[0]
            mid_ends[1, 1] -= self.leg_y_offset[1]
            mid_ends[:, -1] = -self.leg_height
            legs += self.make_limb(mid_ends, mid_starts)

        return legs

    def make_limb(self, leg_ends, leg_starts):
        limbs = []
        for leg_start, leg_end in zip(leg_starts, leg_ends):
            axes = None
            scale = None
            limb = align_bezier(
                np.stack([leg_start, leg_end], -1),
                axes, scale
            )
            limb.location = (
                np.array([
                    1 if leg_start[0] < 0 else -1,
                    1 if leg_start[1] < -self.size / 2 else -1,
                    0,
                ]) * self.leg_thickness / 2
            )
            apply_transform(limb, loc=True)
            limbs.append(limb)
        return limbs

    # ── Backs ──
    def make_backs(self):
        back_starts = (
            np.array([[-self.seat_back, 0, 0], [self.seat_back, 0, 0]]) * self.width / 2
        )
        back_ends = back_starts.copy()
        back_ends[:, 0] += np.array([self.back_x_offset, -self.back_x_offset])
        back_ends[:, 1] = self.back_y_offset
        back_ends[:, 2] = self.back_height
        return self.make_limb(back_starts, back_ends)

    # ── Solidify limbs ──
    def solidify_limb(self, obj, axis, thickness=None):
        if thickness is None:
            thickness = self.leg_thickness
        if self.is_leg_round:
            solidify_cross_section(obj, axis, thickness)
            modify_mesh(obj, 'BEVEL', width=self.bevel_width, segments=8)
        else:
            apply_geo_radius(obj, thickness / 2, 32)
        return obj

    # ── Leg decorations ──
    def make_leg_decors(self, legs):
        if self.leg_decor_type == "none":
            return self._make_leg_bar_decors(legs)

        obj = join_objects([deep_clone_obj(l) for l in legs])
        x, y, z = read_co(obj).T
        z = np.maximum(z, -self.leg_height * uniform(0.7, 0.9))
        write_co(obj, np.stack([x, y, z], -1))
        with ViewportMode(obj, 'EDIT'):
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.convex_hull()
            bpy.ops.mesh.normals_make_consistent(inside=False)

        remove_faces(obj, np.abs(read_normal(obj)[:, -1]) > 0.5)

        if self.leg_decor_wrapped:
            x, y, z = read_co(obj).T
            x[x < 0] -= self.leg_thickness / 2 + 1e-3
            x[x > 0] += self.leg_thickness / 2 + 1e-3
            y[y < -self.size / 2] -= self.leg_thickness / 2 + 1e-3
            y[y > -self.size / 2] += self.leg_thickness / 2 + 1e-3
            write_co(obj, np.stack([x, y, z], -1))

        dissolve_limited(obj)

        match self.leg_decor_type:
            case "coiled":
                self.divide(obj, self.dot_distance)
                make_coiled(obj, self.dot_distance, self.dot_depth, self.dot_size)
            case "pad":
                co_before = read_co(obj)
                bb_min, bb_max = np.amin(co_before, 0), np.amax(co_before, 0)
                self.divide(obj, self.panel_distance)
                with ViewportMode(obj, 'EDIT'):
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.inset(
                        thickness=self.panel_margin,
                        depth=self.panel_margin,
                        use_individual=True,
                    )
                co_after = read_co(obj)
                co_after = np.clip(co_after, bb_min - 0.5, bb_max + 0.5)
                write_co(obj, co_after)
                modify_mesh(obj, 'BEVEL', segments=4)

        return [obj]

    def _make_leg_bar_decors(self, legs):
        decors = []
        if self.has_leg_x_bar:
            z_height = -self.leg_height * uniform(*self.leg_offset_bar)
            locs = []
            for leg in legs[:4]:
                co = read_co(leg)
                locs.append(co[np.argmin(np.abs(co[:, -1] - z_height))])
            decors.append(
                self.solidify_limb(bezier_curve(np.stack([locs[0], locs[3]], -1)), 0)
            )
            decors.append(
                self.solidify_limb(bezier_curve(np.stack([locs[1], locs[2]], -1)), 0)
            )
        if self.has_leg_y_bar:
            z_height = -self.leg_height * uniform(*self.leg_offset_bar)
            locs = []
            for leg in legs[:4]:
                co = read_co(leg)
                locs.append(co[np.argmin(np.abs(co[:, -1] - z_height))])
            decors.append(
                self.solidify_limb(bezier_curve(np.stack([locs[0], locs[1]], -1)), 1)
            )
            decors.append(
                self.solidify_limb(bezier_curve(np.stack([locs[2], locs[3]], -1)), 1)
            )
        return decors

    def divide(self, obj, distance):
        for i, dim_size in enumerate(obj.dimensions):
            axis = np.zeros(3)
            axis[i] = 1
            d = distance if i != 2 else distance * uniform(0.5, 1.0)
            cuts = int(np.ceil(dim_size / d))
            if cuts > 0:
                subdivide_edge_ring(obj, cuts, axis)

    # ── Back decorations ──
    def make_back_decors(self, backs):
        obj = join_objects([deep_clone_obj(b) for b in backs])
        x, y, z = read_co(obj).T
        x += np.where(x > 0, self.back_thickness / 2, -self.back_thickness / 2)
        write_co(obj, np.stack([x, y, z], -1))

        smoothness = uniform(0, 1)
        profile_shape_factor = uniform(0, 0.4)

        with ViewportMode(obj, 'EDIT'):
            bpy.ops.mesh.select_mode(type='EDGE')
            center = read_edge_center(obj)
            for z_min, z_max in self.back_profile:
                select_edges(
                    obj,
                    (z_min * self.back_height <= center[:, -1])
                    & (center[:, -1] <= z_max * self.back_height),
                )
                bpy.ops.mesh.bridge_edge_loops(
                    number_cuts=64,
                    interpolation='LINEAR',
                    smoothness=smoothness,
                    profile_shape_factor=profile_shape_factor,
                )
            bpy.ops.mesh.select_loose()
            bpy.ops.mesh.delete()

        modify_mesh(
            obj, 'SOLIDIFY',
            thickness=np.minimum(self.thickness, self.back_thickness),
            offset=0,
        )

        parts = [obj]

        if self.back_type == "vertical-bar":
            other = join_objects([deep_clone_obj(b) for b in backs])
            with ViewportMode(other, 'EDIT'):
                bpy.ops.mesh.select_mode(type='EDGE')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.bridge_edge_loops(
                    number_cuts=self.back_vertical_cuts,
                    interpolation='LINEAR',
                    smoothness=smoothness,
                    profile_shape_factor=profile_shape_factor,
                )
                bpy.ops.mesh.select_all(action='INVERT')
                bpy.ops.mesh.delete()
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.delete(type='ONLY_FACE')
            remove_edges(other, np.abs(read_edge_direction(other)[:, -1]) < 0.5)
            remove_vertices(other, lambda x, y, z: z < -self.thickness / 2)
            remove_vertices(
                other,
                lambda x, y, z: z > (self.back_profile[0][0] + self.back_profile[0][1])
                    * self.back_height / 2,
            )
            self.solidify_limb(other, 2, self.back_thickness)
            parts.append(other)
        elif self.back_type == "partial":
            co = read_co(obj)
            co[:, 1] *= self.back_partial_scale
            write_co(obj, co)

        modify_mesh(obj, 'BEVEL', width=self.bevel_width, segments=8)

        match self.back_type:
            case "coiled":
                back_obj = self._make_back_solid(backs)
                self.divide(back_obj, self.dot_distance)
                make_coiled(back_obj, self.dot_distance, self.dot_depth, self.dot_size)
                back_obj.scale = (1 - 1e-3,) * 3
                apply_transform(back_obj)
                with ViewportMode(parts[0], 'EDIT'):
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.bisect(
                        plane_co=(0, 0, self.back_height),
                        plane_no=(0, 0, 1),
                        clear_inner=True,
                    )
                return [back_obj] + parts
            case "pad":
                back_obj = self._make_back_solid(backs)
                co_before = read_co(back_obj)
                bb_min, bb_max = np.amin(co_before, 0), np.amax(co_before, 0)
                self.divide(back_obj, self.panel_distance)
                select_faces(back_obj, np.abs(read_normal(back_obj)[:, 1]) > 0.5)
                with ViewportMode(back_obj, 'EDIT'):
                    bpy.ops.mesh.inset(
                        thickness=self.panel_margin,
                        depth=self.panel_margin,
                        use_individual=True,
                    )
                co_after = read_co(back_obj)
                co_after = np.clip(co_after, bb_min - 0.5, bb_max + 0.5)
                write_co(back_obj, co_after)
                modify_mesh(back_obj, 'BEVEL', segments=4)
                back_obj.scale = (1 - 1e-3,) * 3
                apply_transform(back_obj)
                with ViewportMode(parts[0], 'EDIT'):
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.bisect(
                        plane_co=(0, 0, self.back_height),
                        plane_no=(0, 0, 1),
                        clear_inner=True,
                    )
                return [back_obj] + parts
            case _:
                return parts

    def _make_back_solid(self, backs):
        obj = join_objects([deep_clone_obj(b) for b in backs])
        with ViewportMode(obj, 'EDIT'):
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.convex_hull()
        modify_mesh(
            obj, 'SOLIDIFY',
            thickness=np.minimum(self.thickness, self.leg_thickness),
            offset=0,
        )
        with ViewportMode(obj, 'EDIT'):
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.normals_make_consistent(inside=False)
        return obj

    # ── Main create ──
    def create_asset(self, mat_surface=None, mat_limb=None, mat_panel=None):
        seat = self.make_seat()
        legs = self.make_legs()
        backs = self.make_backs()

        parts = [seat] + legs + backs

        leg_decor_parts = self.make_leg_decors(legs)
        parts.extend(leg_decor_parts)

        back_decor_parts = self.make_back_decors(backs)
        parts.extend(back_decor_parts)

        for leg in legs:
            self.solidify_limb(leg, 2)

        for back in backs:
            self.solidify_limb(back, 2, self.back_thickness)

        # Per-part material binding (before final join) — mirrors chair.py:197-199
        if mat_surface is not None:
            seat.data.materials.append(mat_surface)
        if mat_limb is not None:
            for leg in legs:
                leg.data.materials.append(mat_limb)
            for back in backs:
                back.data.materials.append(mat_limb)
            if self.leg_decor_type in ("plain", "legs"):
                for d in leg_decor_parts:
                    d.data.materials.append(mat_limb)
        if mat_panel is not None:
            if self.leg_decor_type in ("coiled", "pad"):
                for d in leg_decor_parts:
                    d.data.materials.append(mat_panel)
            for d in back_decor_parts:
                d.data.materials.append(mat_panel)

        obj = join_objects(parts)
        obj.rotation_euler.z += np.pi / 2
        apply_transform(obj)
        return obj

# ═══════════════════════════════════════════════════════════════════
#  Mattress creation (inlined from MattressFactory.py)
# ═══════════════════════════════════════════════════════════════════

def create_mattress(mat_width, mat_size, mat_thickness, mattress_type,
                    dot_distance, dot_depth, dot_size, wrap_distance=0.05):
    """Create a mattress mesh. Returns the object."""

    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.scale = (mat_width / 2, mat_size / 2, mat_thickness / 2)
    apply_transform(obj, True)

    if mattress_type == "coiled":
        for i, dim_size in enumerate(obj.dimensions):
            axis = np.zeros(3)
            axis[i] = 1
            subdivide_edge_ring(obj, int(np.ceil(dim_size / dot_distance)), axis)
        make_coiled(obj, dot_distance, dot_depth, dot_size)

    elif mattress_type == "wrapped":
        for i, dim_size in enumerate([mat_width, mat_size, mat_thickness]):
            axis = np.zeros(3)
            axis[i] = 1
            subdivide_edge_ring(obj, int(np.ceil(dim_size / wrap_distance)), axis)
        modify_mesh(obj, 'BEVEL', width=wrap_distance / 3, segments=2)
        # Pin bottom vertices
        vg = obj.vertex_groups.new(name="pin")
        co = read_co(obj)
        pin_verts = np.nonzero(co[:, -1] < 1e-1 - mat_thickness / 2)[0].tolist()
        vg.add(pin_verts, 1, "REPLACE")
        cloth_sim(
            obj,
            gravity=0,
            use_pressure=True,
            uniform_pressure_force=uniform(0.1, 0.2),
            vertex_group_mass="pin",
        )

    obj.name = "Mattress"
    obj.data.materials.append(MAT_MATTRESS)
    return obj

# ═══════════════════════════════════════════════════════════════════
#  Pillow creation (inlined from PillowFactory.py, simplified)
# ═══════════════════════════════════════════════════════════════════

def create_pillow(pillow_seed=None):
    """Create a single pillow mesh. Returns the object."""

    if pillow_seed is not None:
        np.random.seed(pillow_seed)
        random.seed(pillow_seed)

    shape = weighted_choice([(4, "square"), (4, "rectangle"), (1, "circle"), (1, "torus")])
    p_width = uniform(0.4, 0.7)
    if shape == "square":
        p_size = p_width
    else:
        p_size = p_width * log_uniform(0.6, 0.8)

    bevel_width = uniform(0.02, 0.05)
    thickness = log_uniform(0.006, 0.008)
    extrude_thickness = thickness * log_uniform(1, 8) if uniform() < 0.5 else 0
    has_seam = uniform() < 0.3 and shape != "torus"
    seam_radius = uniform(0.01, 0.02)

    if shape == "circle":
        bpy.ops.mesh.primitive_circle_add(vertices=128, radius=1.0, location=(0, 0, 0))
        obj = bpy.context.active_object
        with ViewportMode(obj, 'EDIT'):
            bpy.ops.mesh.fill_grid()
    elif shape == "torus":
        bpy.ops.mesh.primitive_circle_add(vertices=128, radius=1.0, location=(0, 0, 0))
        outer = bpy.context.active_object
        bpy.ops.mesh.primitive_circle_add(vertices=128, radius=uniform(0.2, 0.4), location=(0, 0, 0))
        inner = bpy.context.active_object
        obj = join_objects([outer, inner])
        with ViewportMode(obj, 'EDIT'):
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.bridge_edge_loops(number_cuts=12, interpolation='LINEAR')
    else:
        obj = new_grid(x_subdivisions=32, y_subdivisions=32)

    obj.scale = (p_width / 2, p_size / 2, 1)
    apply_transform(obj, True)

    # Solidify
    modify_mesh(obj, 'SOLIDIFY', thickness=thickness, offset=0)

    # Pin vertex group for seam
    group = obj.vertex_groups.new(name="pin")
    if has_seam:
        with ViewportMode(obj, 'EDIT'):
            bpy.ops.mesh.select_mode(type='FACE')
            # Select faces near center top
            bm = bmesh.from_edit_mesh(obj.data)
            bm.faces.ensure_lookup_table()
            bpy.ops.mesh.select_all(action='DESELECT')
            centers = read_center(obj)
            mask = (centers[:, 0]**2 + centers[:, 1]**2 < seam_radius**2) & (centers[:, 2] > 0)
            for i in np.nonzero(mask)[0]:
                bm.faces[i].select_set(True)
            bm.select_flush(False)
            bmesh.update_edit_mesh(obj.data)
            bpy.ops.mesh.region_to_loop()
            bpy.ops.mesh.select_mode(type='VERT')
        # Read selection
        sel = np.zeros(len(obj.data.vertices), dtype=int)
        obj.data.vertices.foreach_get("select", sel)
        group.add(np.nonzero(sel)[0].tolist(), 1, "REPLACE")

    # Cloth sim
    if shape == "torus":
        pressure = uniform(8, 12)
    else:
        pressure = uniform(1, 2)

    cloth_sim(
        obj,
        tension_stiffness=uniform(0, 5),
        gravity=0,
        use_pressure=True,
        uniform_pressure_force=pressure,
        vertex_group_mass="pin" if has_seam else "",
    )

    # Optional extrude
    if extrude_thickness > 0:
        with ViewportMode(obj, 'EDIT'):
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.extrude_region_shrink_fatten(
                TRANSFORM_OT_shrink_fatten={"value": extrude_thickness}
            )

    # Center
    bb_min = Vector(obj.bound_box[0])
    bb_max = Vector(obj.bound_box[6])
    c = (bb_min + bb_max) / 2.0
    obj.location = (-c.x, -c.y, -c.z)
    apply_transform(obj, True)

    # Subsurf
    subsurf(obj, 2)

    obj.name = "Pillow"
    obj.data.materials.append(MAT_PILLOW)
    return obj

# ═══════════════════════════════════════════════════════════════════
#  Sheet/blanket creation (simplified flat grid approach)
# ═══════════════════════════════════════════════════════════════════

def create_sheet(sheet_width, sheet_size, sheet_type):
    """Create a sheet/blanket as a subdivided flat grid.
    sheet_type controls pressure: quilt=0, comforter=small, box_comforter=large.
    Returns the sheet object.
    """
    # Calculate subdivisions proportional to size
    x_sub = max(32, int(sheet_width / sheet_size * 64))
    y_sub = max(32, int(sheet_size / sheet_width * 64))
    # Clamp for performance
    x_sub = min(x_sub, 64)
    y_sub = min(y_sub, 64)

    obj = new_grid(x_subdivisions=x_sub, y_subdivisions=y_sub)
    obj.scale = (sheet_width / 2, sheet_size / 2, 1)
    apply_transform(obj, True)

    # For comforter/box_comforter, add solidify to give it some thickness
    if sheet_type in ("comforter", "box_comforter"):
        modify_mesh(obj, 'SOLIDIFY', thickness=0.01)

    # For box_comforter, create the grid pinch pattern
    if sheet_type == "box_comforter":
        margin = uniform(0.3, 0.4)
        x, y, _ = read_co(obj).T
        _x = (np.abs(x / margin - np.round(x / margin)) * margin
              < sheet_width / 64 / 2)
        _y = (np.abs(y / margin - np.round(y / margin)) * margin
              < sheet_width / 64 / 2)
        with ViewportMode(obj, 'EDIT'):
            bm = bmesh.from_edit_mesh(obj.data)
            bm.verts.ensure_lookup_table()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_mode(type='VERT')
            co = read_co(obj)
            _x2 = (np.abs(co[:, 0] / margin - np.round(co[:, 0] / margin)) * margin
                   < sheet_width / 64 / 2)
            _y2 = (np.abs(co[:, 1] / margin - np.round(co[:, 1] / margin)) * margin
                   < sheet_width / 64 / 2)
            mask = _x2 | _y2
            for i in np.nonzero(mask)[0]:
                bm.verts[i].select_set(True)
            bm.select_flush(False)
            bmesh.update_edit_mesh(obj.data)
            bpy.ops.mesh.remove_doubles(threshold=0.02)

    obj.name = "Sheet"
    obj.data.materials.append(MAT_SHEET)
    return obj

# ═══════════════════════════════════════════════════════════════════
#  BedFactory — Main assembly
# ═══════════════════════════════════════════════════════════════════

# Save/restore seed so sub-components get reproducible but varied seeds
master_rng_state = np.random.get_state()

# ── 1. Create bed frame ──
frame_factory = BedFrameFactory(SEED)
frame = frame_factory.create_asset(
    mat_surface=MAT_SURFACE,
    mat_limb=MAT_LIMB,
    mat_panel=MAT_PANEL,
)
frame.name = "BedFrame"
# Apply wear_tear to the bedframe only (mirrors BedFrameFactory.finalize_assets
# behavior in the converted BedFrameFactory.py template).
if WEAR_DO_SCRATCH:  apply_scratches(frame)
if WEAR_DO_EDGEWEAR: apply_edge_wear(frame)

# After frame creation, the frame is rotated by pi/2.
# Record key dimensions from the factory (pre-rotation coordinates):
frame_width = frame_factory.width
frame_size = frame_factory.size
frame_thickness = frame_factory.thickness
frame_leg_height = frame_factory.leg_height

# Restore master seed state with an offset for mattress params
np.random.seed(SEED + 1000)
random.seed(SEED + 1000)

# ── 2. Create mattress ──
mattress_type = weighted_choice([(1, "coiled"), (3, "wrapped")])
mat_width = frame_width * uniform(0.88, 0.96)
mat_size = frame_size * uniform(0.88, 0.96)
mat_thickness = uniform(0.2, 0.35)
dot_distance = log_uniform(0.16, 0.2)
dot_size = uniform(0.005, 0.02)
dot_depth = uniform(0.04, 0.08)

mattress = create_mattress(mat_width, mat_size, mat_thickness, mattress_type,
                           dot_distance, dot_depth, dot_size)

# Position mattress on top of frame
# The frame is rotated pi/2 around Z. In the original code:
#   mattress.location = (size/2, 0, mat_thickness/2)
#   mattress.rotation_euler[-1] = pi/2
# After the frame's pi/2 rotation, the frame's local X becomes world Y
# and local Y becomes world -X. But since we already applied the transform,
# the frame is in world coordinates with the bed aligned along Y.
#
# The frame seat top is at z=0 (frame_thickness/2 up from seat center,
# minus thickness/2). The mattress should sit on top.
# After frame rotation: the frame extends from about -size/2 to +size/2 in X
# and -width/2 to +width/2 in Y.
mattress.location = (frame_size / 2, 0, mat_thickness / 2)
mattress.rotation_euler[2] = np.pi / 2
apply_transform(mattress, True)

# ── 3. Create sheet/blanket ──
np.random.seed(SEED + 2000)
random.seed(SEED + 2000)

sheet_type = weighted_choice([
    (4, "quilt"), (4, "comforter"), (4, "box_comforter"), (1, "none")
])
sheet_folded = uniform() < 0.5

if sheet_type != "none":
    # Determine sheet dimensions
    match sheet_type:
        case "quilt":
            sheet_width = mat_width * uniform(1.4, 1.6)
            sheet_size = mat_size * uniform(0.9, 1.1)
            pressure = 0
        case "comforter":
            sheet_width = mat_width * uniform(1.4, 1.8)
            sheet_size = mat_size * uniform(0.9, 1.2)
            pressure = uniform(1.0, 1.5)
        case "box_comforter":
            sheet_width = mat_width * uniform(1.4, 1.8)
            sheet_size = mat_size * uniform(0.9, 1.2)
            pressure = log_uniform(8, 15)
        case _:
            sheet_width = mat_width * uniform(1.4, 1.6)
            sheet_size = mat_size * uniform(0.9, 1.1)
            pressure = 0

    sheet = create_sheet(sheet_width, sheet_size, sheet_type)

    # Fold if requested (simplified fold: bisect + mirror Y half)
    if sheet_folded:
        theta = uniform(-np.pi / 6, np.pi / 6)
        y_margin = sheet_size * (0.5 - uniform(0.1, 0.3))
        sheet.rotation_euler[2] = theta
        sheet.location[1] -= y_margin
        apply_transform(sheet, True)
        with ViewportMode(sheet, 'EDIT'):
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.bisect(plane_co=(0, 0, 0), plane_no=(0, 1, 0))
        x, y, z = read_co(sheet).T
        co = np.stack([x, np.where(y > 0, -y, y), np.where(y > 0, 0.05 - z, z)], -1)
        write_co(sheet, co)
        sheet.location[1] += y_margin
        apply_transform(sheet, True)
        sheet.rotation_euler[2] = -theta
        apply_transform(sheet)

    # Position sheet over mattress
    z_sheet = mattress.location[2] + np.max(read_co(mattress)[:, -1])
    sheet.location = (sheet_size / 2 + uniform(0, 0.15), 0, z_sheet)
    sheet.rotation_euler[2] = np.pi / 2
    apply_transform(sheet, True)

    # Cloth sim to drape sheet over mattress and frame
    cloth_sim(
        sheet,
        [mattress, frame],
        mass=0.05,
        tension_stiffness=2,
        distance_min=5e-3,
        use_pressure=True,
        uniform_pressure_force=pressure,
        use_self_collision=sheet_folded,
    )
    subsurf(sheet, 2)
else:
    # No sheet — create a dummy empty mesh
    bpy.ops.mesh.primitive_plane_add(location=(0, 0, -100))
    sheet = bpy.context.active_object
    sheet.name = "Sheet"
    sheet.data.materials.append(MAT_SHEET)

# ── 4. Create cover (simplified: another flat grid draped on top) ──
np.random.seed(SEED + 3000)
random.seed(SEED + 3000)

has_cover = uniform() < 0.5
if has_cover and sheet_type != "none":
    cover_width = mat_width * uniform(1.6, 1.8)
    cover_size = mat_size * uniform(0.3, 0.4)

    cover = new_grid(x_subdivisions=32, y_subdivisions=32)
    cover.scale = (cover_width / 2, cover_size / 2, 1)
    apply_transform(cover, True)
    cover.name = "Cover"
    cover.data.materials.append(MAT_COVER)

    # Position cover over sheet
    z_cover = sheet.location[2] + np.max(read_co(sheet)[:, -1])
    cover.location = (frame_size / 2 + uniform(0, 0.3), 0, z_cover)
    cover.rotation_euler[2] = np.pi / 2
    apply_transform(cover, True)

    # Cloth sim
    cloth_sim(
        cover,
        [sheet, mattress],
        80,
        mass=0.05,
        tension_stiffness=2,
        distance_min=5e-3,
    )
    subsurf(cover, 2)
else:
    cover = None

# ── 5. Create pillows ──
np.random.seed(SEED + 4000)
random.seed(SEED + 4000)

n_pillows = np.random.randint(2, 4)

pillows = []
for pi in range(n_pillows):
    pillow_seed = SEED + 5000 + pi * 100
    p = create_pillow(pillow_seed)
    p.name = f"Pillow_{pi}"
    pillows.append(p)

# Place pillows on top of mattress near the head of the bed
# After frame rotation, the head of the bed is at positive X.
# We place pillows at x = uniform(0.1, 0.4) * frame_size (near head)
# and y = uniform(-0.3, 0.3) * frame_width
np.random.seed(SEED + 6000)
random.seed(SEED + 6000)

# Generate candidate positions
n_candidates = 10
cand_x = uniform(0.1, 0.4, n_candidates) * frame_size
cand_y = uniform(-0.3, 0.3, n_candidates) * frame_width

# Pick n_pillows spread-out positions using simple decimation
# (pick the ones that are most spread out)
def decimate_points(points, n):
    """Select n well-separated points from candidates."""

    if len(points) <= n:
        return points
    selected = [0]
    for _ in range(n - 1):
        max_min_dist = -1
        best_idx = -1
        for i in range(len(points)):
            if i in selected:
                continue
            min_dist = min(np.linalg.norm(points[i] - points[j]) for j in selected)
            if min_dist > max_min_dist:
                max_min_dist = min_dist
                best_idx = i
        if best_idx >= 0:
            selected.append(best_idx)
    return points[selected]

candidates = np.stack([cand_x, cand_y, np.ones(n_candidates)], -1)
pillow_locs = decimate_points(candidates, n_pillows)

# Helper: find local surface Z at a given XY position using raycast
def find_surface_z(objs, x, y):
    """Find the top surface Z at (x, y) by raycasting from above.
    Shoots a ray from (x, y, 100) downward to find the first surface hit.
    This correctly handles draped sheets where top and side surfaces overlap in XY."""

    best_z = -np.inf
    for obj in objs:
        if obj is None:
            continue
        # All transforms are applied, so local space = world space
        success, hit_loc, _, _ = obj.ray_cast((x, y, 100.0), (0, 0, -1))
        if success:
            best_z = max(best_z, hit_loc[2])
    if best_z == -np.inf:
        # Fallback: use nearest vertex Z if raycast misses all surfaces
        for obj in objs:
            if obj is None:
                continue
            co = read_co(obj)
            dist_xy = np.sqrt((co[:, 0] - x)**2 + (co[:, 1] - y)**2)
            best_z = max(best_z, co[np.argmin(dist_xy), 2])
    return best_z

# Place each pillow
for pi, (p, loc) in enumerate(zip(pillows, pillow_locs)):
    # Find local surface Z at this pillow's XY position
    # Include cover if it exists (it sits on top of the sheet)
    surface_objs = [mattress]
    if sheet_type != "none":
        surface_objs.append(sheet)
    if cover is not None:
        surface_objs.append(cover)
    z_base = find_surface_z(surface_objs, loc[0], loc[1])

    # The pillow bottom is curved from cloth sim — only the very lowest vertex
    # is at min Z, while the visible bottom area is higher. Use a representative
    # bottom height (10th percentile) and sink slightly into the surface to ensure
    # visual contact rather than floating.
    pco = read_co(p)
    bottom_z = np.percentile(pco[:, 2], 5)  # 5th percentile = representative bottom
    p.location = (loc[0], loc[1], z_base - 0.005 - bottom_z)
    p.rotation_euler[2] = uniform(0, np.pi)
    apply_transform(p, True)

# ── 6. Parent everything to frame ──
mattress.parent = frame
sheet.parent = frame
if cover is not None:
    cover.parent = frame
for p in pillows:
    p.parent = frame

select_none()

# Name the frame
frame.name = "BedFactory"

# Shade smooth all parts
for obj in [frame, mattress, sheet] + ([cover] if cover is not None else []) + pillows:
    if obj is not None and obj.type == 'MESH':
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.shade_smooth()
        obj.select_set(False)

# Update mesh
frame.data.update()

# Count total verts
total_verts = len(frame.data.vertices)
total_faces = len(frame.data.polygons)
child_verts = 0
child_faces = 0
for child in frame.children:
    if child.type == 'MESH':
        child.data.update()
        child_verts += len(child.data.vertices)
        child_faces += len(child.data.polygons)

