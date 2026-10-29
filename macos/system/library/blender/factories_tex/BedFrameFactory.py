# [FL_INDEX: keywords="blender_factory, procedural_3d, BedFrameFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BedFrameFactory | Category: factories_tex
# Prompt: A 3D model of a wooden bed frame rendered from an elevated three-quarter perspective, featuring a tall decorative headboard with carved or molded panel details, a shorter footboard, four tapered legs with metallic accents, and an open slatted support structure across the sleeping surface.

import os
import bpy, bmesh, math
import random, colorsys
import numpy as np
from numpy.random import uniform

# ----------------------------------------------------------------------------

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

# wear_tear post-processing — faithful raw-bpy translation
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

# ── Seed (will be overridden by Phase 1) ──
SEED = int(os.environ.get('SEED', 0))
random.seed(SEED)
np.random.seed(SEED)

# ── Scene cleanup ──
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
for c in list(bpy.data.collections):
    if c != bpy.context.scene.collection:
        bpy.data.collections.remove(c)
for ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(ng)
bpy.context.scene.cursor.location = (0, 0, 0)

# FixedSeed(factory_seed)). Material sampling order follows bedframe.py:71-82:
#   1. surface = weighted_sample(bedframe)
#   2. limb_surface = weighted_sample(furniture_hard_surface)
#   3. scratch gate
#   4. edge_wear gate
# bedframe.py does NOT sample a separate panel surface (unlike ChairFactory),
# so we bind the same surface material to panel parts.
seed_all(SEED)
MAT_SURFACE    = get_material("bedframe", "Surface")
MAT_LIMB       = get_material("furniture_hard_surface", "Limb")
MAT_PANEL      = MAT_SURFACE    # bedframe uses surface for panels too
_scratch_p, _edge_wear_p = WEAR_TEAR_PROB
WEAR_DO_SCRATCH  = (np.random.uniform() <= _scratch_p)
WEAR_DO_EDGEWEAR = (np.random.uniform() <= _edge_wear_p)

# --- Original geometry code (copied verbatim from objects_blender/seating/
#     BedFrameFactory.py, lines 24-996), with material bindings added in
#     create_asset() before the final join. ====================================

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
    bpy.context.collection.objects.link(new_obj)
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
    """Create bezier curve from anchor points, optionally convert to mesh."""

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
    """Convert bezier curve to mesh with adaptive subdivision for smooth curves."""

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
    """Create bezier curve then adjust handle positions based on axes and scale."""

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
    curve_circle.inputs['Radius'].default_value = radius

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
    """Create coiled dimple pattern on the surface of obj."""

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

#  BedFrameFactory (geometry unchanged from objects_blender/ source)

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

    # ── Backs (two posts) ──
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

        # --- Per-part material binding (before final join) ---
        # Mirrors chair.py:197-199:
        #   surface.assign_material(obj, self.surface)                     # whole
        #   surface.assign_material(obj, self.panel_surface, "panel")      # decors
        #   surface.assign_material(obj, self.limb_surface, "limb")        # legs/back posts
        # bedframe.py does not re-sample panel_surface, so MAT_PANEL == MAT_SURFACE.
        if mat_surface is not None:
            seat.data.materials.append(mat_surface)
        if mat_limb is not None:
            for leg in legs:
                leg.data.materials.append(mat_limb)
            for back in backs:
                back.data.materials.append(mat_limb)
            # Bar decors from _make_leg_bar_decors are solidified limbs — also limb mat
            if self.leg_decor_type in ("plain", "legs"):
                for d in leg_decor_parts:
                    d.data.materials.append(mat_limb)
        if mat_panel is not None:
            # Leg decor panels (coiled/pad) — they are the "panel"-tagged geometry
            if self.leg_decor_type in ("coiled", "pad"):
                for d in leg_decor_parts:
                    d.data.materials.append(mat_panel)
            # Back decor: first element is the panel face in coiled/pad modes.
            # For other back types the first element is the base back panel.
            for d in back_decor_parts:
                d.data.materials.append(mat_panel)

        obj = join_objects(parts)
        obj.rotation_euler.z += np.pi / 2
        apply_transform(obj)
        return obj

#  Main — sample_params equivalent lives in __init__; just call build().

def build(seed=SEED):
    # materials are already captured in module-level MAT_* variables.
    factory = BedFrameFactory(seed)
    obj = factory.create_asset(
        mat_surface=MAT_SURFACE,
        mat_limb=MAT_LIMB,
        mat_panel=MAT_PANEL,
    )
    if obj is not None:
        obj.name = "BedFrameFactory"
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.shade_smooth()
        obj.select_set(False)
        obj.data.update()
        # wear_tear post-processing — finalize_assets mirror
        if WEAR_DO_SCRATCH:  apply_scratches(obj)
        if WEAR_DO_EDGEWEAR: apply_edge_wear(obj)
    return obj

build(SEED)

