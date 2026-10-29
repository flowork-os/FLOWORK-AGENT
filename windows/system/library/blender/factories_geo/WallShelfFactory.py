# [FL_INDEX: keywords="blender_factory, procedural_3d, WallShelfFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: WallShelfFactory | Category: factories_geo
# Prompt: A 3D model of a wall shelf rendered from a front-above perspective. The shelf features a flat horizontal rectangular board in dark black with two symmetrically placed rounded arch-shaped bracket supports rising from the board surface, rendered in a contrasting muted purple-mauve color.

"""WallShelfFactory — textured conversion.

Geometry copied verbatim from
    objects_blender/wall_decorations/WallShelfFactory.py.

Materials faithfully re-implement the shaders referenced by

    plate_surfaces    = ("weighted_choice",
                         (10,  wood.Wood),
                         (3.0, metal.MetalBasic),
                         (2.0, metal.BrushedMetal),
                         (1.0, metal.GalvanizedMetal),
                         (1.0, metal.GrainedMetal),
                         (0.7, metal.HammeredMetal),
                         (0.3, metal.BrushedBlackMetal))
    support_surfaces  = ("weighted_choice",
                         (3.0, metal.MetalBasic),
                         (2.0, metal.BrushedMetal),
                         (1.0, metal.GalvanizedMetal),
                         (1.0, metal.GrainedMetal),
                         (0.7, metal.HammeredMetal),
                         (0.3, metal.BrushedBlackMetal),
                         (5,   wood.Wood),
                         (5,   plastic.PlasticRough))

Shader sources faithfully ported from:
                                                        -> make_grained_metal
                                                        -> make_brushed_black_metal

wall_shelf.py does NOT implement finalize_assets() and does not apply
wear_tear, so this textured script also skips any scratch / edge_wear stage.
"""
# SEED-deterministic: all random calls seeded from SEED

import os
import math
import random
import colorsys

import bmesh
import bpy
import numpy as np

# ============================================================================
# ============================================================================

def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def _mat_log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

_NATURAL_BASE_HSV = [
    (0.0,    0.0,    0.5271),  # 0xC0C0C0 silver
    (0.0961, 0.6702, 0.2623),  # 0x8C7853 khaki
    (0.1319, 0.1682, 0.5089),  # 0xBDBAAE light gray
    (0.6296, 0.1518, 0.4678),  # 0xA9ACB6 gray-blue
    (0.0749, 0.1518, 0.4678),  # 0xB6AFA9 gray-beige
]

def metal_natural_hsv():
    
    idx = np.random.randint(0, len(_NATURAL_BASE_HSV))
    h, s, v = _NATURAL_BASE_HSV[idx]
    return (
        h + float(np.random.uniform(-0.1, 0.1)),
        s + float(np.random.uniform(-0.1, 0.1)),
        v * float(_mat_log_uniform(0.2, 0.5)),
    )

def metal_hsv():
    
    if np.random.uniform() < 0.2:
        return metal_natural_hsv()
    return (float(np.random.uniform(0, 1)),
            float(np.random.uniform(0.3, 0.6)),
            _mat_log_uniform(0.02, 0.5))

def bark_hsv():
    
    wood_hex = ["#8b5a2b", "#a0522d", "#cd853f", "#d2691e",
                "#6b4423", "#5d4037", "#7b3f00"]
    h_str = wood_hex[np.random.randint(0, len(wood_hex))].lstrip("#")
    r, g, b = (int(h_str[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return colorsys.rgb_to_hsv(r, g, b)

def _new_material(name: str) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    return mat

def _set_principled(bsdf, **kw):
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

def _rgba_mix(nt, fac_socket, color_a, color_b_value):
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    mix.inputs["Fac"].default_value = 0.5
    if fac_socket is not None:
        nt.links.new(fac_socket, mix.inputs["Fac"])
    if isinstance(color_a, bpy.types.NodeSocket):
        nt.links.new(color_a, mix.inputs["Color1"])
    else:
        mix.inputs["Color1"].default_value = color_a
    mix.inputs["Color2"].default_value = color_b_value
    # Older Blenders expose MixRGB as a single "Color" output; some builds
    # also expose index 2 — use whichever exists.
    return mix

# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
def make_wood(name="Wood") -> bpy.types.Material:
    h, s, v = bark_hsv()
    color = hsv2rgba((h + float(np.random.uniform(-0.0, 0.05)),
                      max(0.0, s + float(np.random.uniform(-0.3, 0.2))),
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

    mix = _rgba_mix(nt, _noise_fac_output(grain), hsv_node.outputs["Color"], color)

    noise_r = nt.nodes.new("ShaderNodeTexNoise")
    noise_r.inputs["Scale"].default_value = _mat_log_uniform(40, 50)
    base_rough = float(np.random.uniform(0.0, 0.4))
    fc = _build_float_curve(nt, _noise_fac_output(noise_r),
                            [(0, base_rough),
                             (1, base_rough + float(np.random.uniform(0.0, 0.8)))])

    mul_disp = nt.nodes.new("ShaderNodeMath")
    mul_disp.operation = "MULTIPLY"
    mul_disp.inputs[1].default_value = _mat_log_uniform(0.0002, 0.01)
    nt.links.new(_noise_fac_output(grain), mul_disp.inputs[0])
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_disp.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Coat Weight": float(np.clip(np.random.uniform(0, 1.4), 0, 1))})
    # MixRGB output "Color" works in all versions
    mix_color_out = mix.outputs.get("Color") or mix.outputs[0]
    nt.links.new(mix_color_out, bsdf.inputs["Base Color"])
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# ----------------------------------------------------------------------------
# make_plastic_rough — port of plastic/plastic_rough.py
# ----------------------------------------------------------------------------
def make_plastic_rough(name="PlasticRough", base_color=None) -> bpy.types.Material:
    if base_color is None:
        base_color = hsv2rgba((float(np.random.uniform(0, 1)),
                               float(np.random.uniform(0.5, 0.8)),
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

# ----------------------------------------------------------------------------
# make_metal_basic — port of metal/metal_basic.py:shader_metal
# ----------------------------------------------------------------------------
def make_metal_basic(name="MetalBasic", color_hsv=None) -> bpy.types.Material:
    if color_hsv is None:
        color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(np.random.uniform(10, 25))
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 2.0
    if "W" in noise.inputs:          noise.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    fc = _build_float_curve(
        nt, _noise_fac_output(noise),
        [(0, float(np.random.uniform(0, 0.2))),
         (1, float(np.random.uniform(0.4, 0.7)))],
    )

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf, Metallic=1.0,
        **{"Specular IOR Level": float(np.random.uniform(0.5, 1.0)),
           "Base Color": hsv2rgba(color_hsv)},
    )
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

# ----------------------------------------------------------------------------
# make_brushed_metal — port of metal/brushed_metal.py
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

# ----------------------------------------------------------------------------
# make_galvanized_metal — port of metal/galvanized_metal.py
# ----------------------------------------------------------------------------
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

# ----------------------------------------------------------------------------
# make_grained_metal — port of metal/grained_and_polished_metal.py
# ----------------------------------------------------------------------------
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

# ----------------------------------------------------------------------------
# make_hammered_metal — port of metal/hammered_metal.py
# ----------------------------------------------------------------------------
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

# ----------------------------------------------------------------------------
# make_brushed_black_metal — port of metal/appliance.py:shader_brushed_black_metal
#   Single anisotropic BSDF at RGB(0.0167, 0.0167, 0.0167).
# ----------------------------------------------------------------------------
def make_brushed_black_metal(name="BrushedBlackMetal") -> bpy.types.Material:
    mat = _new_material(name)
    nt = mat.node_tree
    # ShaderNodeBsdfAnisotropic maps to Glossy BSDF in modern Blender.
    try:
        aniso = nt.nodes.new("ShaderNodeBsdfAnisotropic")
    except RuntimeError:
        aniso = nt.nodes.new("ShaderNodeBsdfGlossy")
    if "Color" in aniso.inputs:
        aniso.inputs["Color"].default_value = (0.0167, 0.0167, 0.0167, 1.0)
    _connect_output(nt, aniso)
    return mat

# ----------------------------------------------------------------------------
# Weighted-choice samplers mirroring wall_shelf.py plate_surfaces /
# "weighted_choice" recursion). Returned callable is invoked by caller.
# ----------------------------------------------------------------------------
_PLATE_SURFACES = [
    (10.0, make_wood),
    (3.0,  make_metal_basic),
    (2.0,  make_brushed_metal),
    (1.0,  make_galvanized_metal),
    (1.0,  make_grained_metal),
    (0.7,  make_hammered_metal),
    (0.3,  make_brushed_black_metal),
]

_SUPPORT_SURFACES = [
    (3.0, make_metal_basic),
    (2.0, make_brushed_metal),
    (1.0, make_galvanized_metal),
    (1.0, make_grained_metal),
    (0.7, make_hammered_metal),
    (0.3, make_brushed_black_metal),
    (5.0, make_wood),
    (5.0, make_plastic_rough),
]

def _weighted_pick(entries):
    weights = np.array([w for w, _ in entries], dtype=float)
    idx = int(np.random.choice(len(entries), p=weights / weights.sum()))
    return entries[idx][1]

# ============================================================================
# === End of inlined material library ========================================
# ============================================================================

SEED = int(os.environ.get("SEED", 0))

def clear_scene():
    bpy.context.scene.cursor.location = (0, 0, 0)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)

def apply_tf(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def join_objs(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

def log_uniform(lo, hi, rng):
    return float(np.exp(rng.uniform(np.log(lo), np.log(hi))))

def make_support_contour(support_length, alpha, support_ratio, n_pts=31):
    """Generate L-shaped + parametric curve support contour points.

    Returns a list of (x, z) 2D points forming the support bracket outline.
    The L has legs along +x and +z axes, with a curved inner edge.
    """
    # L-shape legs: (support_length, 0) -> (0, 0) -> (0, support_length)
    # Parametric curve: r = 1/((cos(t)^a + sin(t)^a)^(1/a)) for t in [0, pi/2]
    theta = np.linspace(0, np.pi / 2, n_pts)
    cos_t = np.cos(theta) + 1e-6
    sin_t = np.sin(theta) + 1e-6
    r = 1.0 / (cos_t**alpha + sin_t**alpha) ** (1.0 / alpha)
    curve_x = r * np.cos(theta) * support_length * support_ratio
    curve_z = r * np.sin(theta) * support_length * support_ratio

    # Build closed contour: L-legs + curve (reversed to close the loop)
    pts = []
    pts.append((support_length, 0.0))
    pts.append((curve_x[0], 0.0))
    for i in range(len(theta)):
        pts.append((curve_x[i], curve_z[i]))
    pts.append((0.0, curve_z[-1]))
    pts.append((0.0, support_length))

    return pts

def make_bracket_mesh(contour_pts, thickness, width):
    """Create a 3D bracket mesh from 2D contour points by buffering and extruding."""

    bm = bmesh.new()
    n = len(contour_pts)

    inner_verts = []
    outer_verts = []

    for i in range(n):
        x, z = contour_pts[i]

        if i == 0:
            dx = contour_pts[1][0] - contour_pts[0][0]
            dz = contour_pts[1][1] - contour_pts[0][1]
        elif i == n - 1:
            dx = contour_pts[-1][0] - contour_pts[-2][0]
            dz = contour_pts[-1][1] - contour_pts[-2][1]
        else:
            dx = contour_pts[i+1][0] - contour_pts[i-1][0]
            dz = contour_pts[i+1][1] - contour_pts[i-1][1]

        length = math.sqrt(dx*dx + dz*dz) + 1e-9
        nx = -dz / length * thickness
        nz = dx / length * thickness

        inner_verts.append(bm.verts.new((x + nx, 0, z + nz)))
        outer_verts.append(bm.verts.new((x - nx, 0, z - nz)))

    for i in range(n - 1):
        bm.faces.new([inner_verts[i], inner_verts[i+1],
                       outer_verts[i+1], outer_verts[i]])

    inner_back = []
    outer_back = []
    for i in range(n):
        co_i = inner_verts[i].co.copy()
        co_o = outer_verts[i].co.copy()
        co_i.y = width
        co_o.y = width
        inner_back.append(bm.verts.new(co_i))
        outer_back.append(bm.verts.new(co_o))

    for i in range(n - 1):
        bm.faces.new([inner_back[i+1], inner_back[i],
                       outer_back[i], outer_back[i+1]])

    for i in range(n - 1):
        bm.faces.new([inner_verts[i], inner_verts[i+1],
                       inner_back[i+1], inner_back[i]])

    for i in range(n - 1):
        bm.faces.new([outer_verts[i+1], outer_verts[i],
                       outer_back[i], outer_back[i+1]])

    bm.faces.new([inner_verts[0], outer_verts[0], outer_back[0], inner_back[0]])
    bm.faces.new([outer_verts[-1], inner_verts[-1], inner_back[-1], outer_back[-1]])

    mesh = bpy.data.meshes.new("bracket")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("bracket", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj

def build(seed=0):
    rng = np.random.default_rng(seed)
    np.random.seed(seed)
    clear_scene()
    # Wipe any cached materials so each build samples fresh.
    for _mat in list(bpy.data.materials):
        bpy.data.materials.remove(_mat)

    # ------------------------------------------------------------------
    # Material sampling — mirrors wall_shelf.py __init__ order:
    #   self.plate_surface   = rg(self.plate_surfaces)()
    #   self.support_surface = rg(self.support_surfaces)()
    # Both consume 1 weighted_choice RNG step from np.random, then the
    # chosen shader consumes its own RNG for colour/roughness.
    # ------------------------------------------------------------------
    plate_ctor   = _weighted_pick(_PLATE_SURFACES)
    plate_mat    = plate_ctor(name="WallShelfPlateMat")
    support_ctor = _weighted_pick(_SUPPORT_SURFACES)
    support_mat  = support_ctor(name="WallShelfSupportMat")

    # Support side
    support_side_choices = ["none", "bottom", "top", "both"]
    support_side_probs = [0.5/4, 1.0/4, 1.0/4, 1.5/4]
    support_side = rng.choice(support_side_choices, p=support_side_probs)

    # Support margin
    use_margin = rng.random() < 1/3
    support_margin = float(rng.uniform(0.0, 0.2)) if use_margin else 0.0

    if support_margin == 0:
        n_support = int(rng.choice([2, 3, 4], p=[0.7, 0.2, 0.1]))
    else:
        n_support = int(rng.choice([2, 3], p=[0.8, 0.2]))

    support_locs = np.linspace(-0.5 + support_margin, 0.5 - support_margin, n_support)

    length = log_uniform(0.3, 0.8, rng)
    width = log_uniform(0.1, 0.2, rng)

    if support_side == "none":
        thickness = log_uniform(0.03, 0.08, rng)
    else:
        thickness = log_uniform(0.01, 0.05, rng)

    support_width = log_uniform(0.01, 0.015, rng)
    support_thickness = support_width * log_uniform(0.4, 1.0, rng)
    support_length = width * float(rng.uniform(0.7, 1.1))

    # Alpha for parametric curve shape
    alpha_choices = ["straight", "curved"]
    alpha_type = rng.choice(alpha_choices, p=[0.5, 0.5])
    if alpha_type == "straight":
        alpha = 1.0
    else:
        sub_choice = rng.random()
        if sub_choice < 0.25:
            alpha = log_uniform(0.4, 0.7, rng)  # concave
        elif sub_choice < 0.75:
            alpha = log_uniform(1.5, 3.0, rng)  # convex
        else:
            alpha = 10.0  # sharp right angle

    support_ratio = float(rng.choice([1.0, float(rng.uniform(0.5, 0.9))], p=[2/3, 1/3]))

    plate_bevel = rng.choice(["none", "front", "side"])

    parts = []

    # Shelf plate (box)
    bm = bmesh.new()
    hw = length / 2
    ht = thickness / 2
    v0 = bm.verts.new((0,     -hw, -ht))
    v1 = bm.verts.new((width, -hw, -ht))
    v2 = bm.verts.new((width,  hw, -ht))
    v3 = bm.verts.new((0,      hw, -ht))
    v4 = bm.verts.new((0,     -hw,  ht))
    v5 = bm.verts.new((width, -hw,  ht))
    v6 = bm.verts.new((width,  hw,  ht))
    v7 = bm.verts.new((0,      hw,  ht))
    bm.faces.new([v0, v1, v2, v3])
    bm.faces.new([v7, v6, v5, v4])
    bm.faces.new([v0, v1, v5, v4])
    bm.faces.new([v1, v2, v6, v5])
    bm.faces.new([v2, v3, v7, v6])
    bm.faces.new([v3, v0, v4, v7])

    plate_mesh = bpy.data.meshes.new("plate")
    bm.to_mesh(plate_mesh)
    bm.free()
    plate = bpy.data.objects.new("plate", plate_mesh)
    bpy.context.scene.collection.objects.link(plate)

    if plate_bevel != "none":
        bv = plate.modifiers.new("bevel", "BEVEL")
        bv.width = float(rng.uniform(0.3, 0.5)) * thickness
        bv.segments = int(rng.integers(4, 9))
        bpy.context.view_layer.objects.active = plate
        bpy.ops.object.modifier_apply(modifier=bv.name)

    apply_tf(plate)
    # Assign plate material BEFORE join so the joined mesh keeps it on
    # the plate faces via material slot indexing.
    plate.data.materials.append(plate_mat)
    parts.append(plate)

    # Support brackets
    if support_side != "none":
        for loc_y in support_locs:
            bracket_y = length * loc_y

            if support_side in ("bottom", "both"):
                contour = make_support_contour(support_length, alpha, support_ratio)
                # Flip Z for bottom bracket
                contour_bottom = [(px, -pz) for px, pz in contour]
                bracket = make_bracket_mesh(contour_bottom, support_thickness / 2, support_width)
                bracket.location = (support_thickness / 2, bracket_y - support_width / 2, 0)
                apply_tf(bracket)
                bracket.data.materials.append(support_mat)
                parts.append(bracket)

            if support_side in ("top", "both"):
                contour = make_support_contour(support_length, alpha, support_ratio)
                bracket = make_bracket_mesh(contour, support_thickness / 2, support_width)
                bracket.location = (support_thickness / 2, bracket_y - support_width / 2, 0)
                apply_tf(bracket)
                bracket.data.materials.append(support_mat)
                parts.append(bracket)

    result = join_objs(parts) if len(parts) > 1 else parts[0]
    result.name = "WallShelfFactory"
    apply_tf(result)

    return result

build(SEED)
