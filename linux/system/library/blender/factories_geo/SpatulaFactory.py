# [FL_INDEX: keywords="blender_factory, procedural_3d, SpatulaFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: SpatulaFactory | Category: factories_geo
# Prompt: A 3D model of a cooking spatula rendered from a slightly elevated top-down perspective. The spatula features a long slender handle that flattens and widens into a broad rectangular head, a dark blue-gray coloring across the entire piece, and a slightly curved or flat working surface on the head with a clean squared-off edge.

# SpatulaFactory — textured standalone Blender script.
# ForkFactory subclass with has_cut=False, wider y_length, shallower z_depth.
# Material: cup registry (body) + wood guard (handle, 40% chance). Wear-tear 50/50.
# Geometry from objects_blender/tableware/SpatulaFactory.py.
# SEED-deterministic: all random calls seeded from SEED

import os
import bpy
import bmesh
import math
import random
import colorsys
import numpy as np
from numpy.random import uniform

# ============================================================================
# === Seed ===================================================================
# ============================================================================

SEED = int(os.environ.get("SEED", 0))

# ============================================================================
# ============================================================================

def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)


def log_uniform(lo, hi, size=None):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi), size)))


# hex -> hex2rgba (srgb_to_linear) -> rgb2hsv
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
        v * float(log_uniform(0.2, 0.5)),
    )


def metal_hsv():
    if np.random.uniform() < 0.2:
        return metal_natural_hsv()
    return (np.random.uniform(0, 1),
            np.random.uniform(0.3, 0.6),
            log_uniform(0.02, 0.5))

def bark_hsv():
    wood_hex = ["#8b5a2b", "#a0522d", "#cd853f", "#d2691e",
                "#6b4423", "#5d4037", "#7b3f00"]
    h_str = wood_hex[np.random.randint(0, len(wood_hex))].lstrip("#")
    r, g, b = (int(h_str[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return colorsys.rgb_to_hsv(r, g, b)


def weighted_sample_mat(reg):
    classes, weights = zip(*reg)
    weights = np.array(weights, dtype=float)
    return classes[int(np.random.choice(len(classes), p=weights / weights.sum()))]


def _new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat


def _set_principled(bsdf, **kw):
    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
    }
    for k, v in kw.items():
        for name in aliases.get(k, (k,)):
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = v
                break


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


def _find_node(nt, bl_idname):
    return next((n for n in nt.nodes if n.bl_idname == bl_idname), None)


def _math(nt, op, in0=None, in1=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    for idx, val in [(0, in0), (1, in1)]:
        if val is None:
            continue
        if hasattr(val, "links"):
            nt.links.new(val, n.inputs[idx])
        else:
            n.inputs[idx].default_value = val
    return n


def _vmath(nt, op, in0=None, in1=None, scale=None):
    n = nt.nodes.new("ShaderNodeVectorMath")
    n.operation = op
    for idx, val in [(0, in0), (1, in1)]:
        if val is None:
            continue
        if hasattr(val, "links"):
            nt.links.new(val, n.inputs[idx])
        else:
            n.inputs[idx].default_value = val
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
    nt.links.new(fac_socket, cr.inputs.get("Fac") or cr.inputs[0])
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


# --- Material makers -------------------------------------------------------

def make_ceramic(name="Ceramic"):
    mat = _new_material(name)
    nt = mat.node_tree
    if np.random.uniform() < 0.8:
        color = hsv2rgba((np.random.uniform(0, 1),
                          np.random.uniform(0.2, 0.4),
                          log_uniform(0.3, 0.6)))
    else:
        color = hsv2rgba((0.0, 0.0, log_uniform(0.3, 0.6)))
    noise_r = nt.nodes.new("ShaderNodeTexNoise")
    noise_r.inputs["Scale"].default_value = log_uniform(20, 40)
    fc_r = _build_float_curve(nt, _noise_fac_output(noise_r), [(0, 0.0), (1, 0.8)])
    noise_c = nt.nodes.new("ShaderNodeTexNoise")
    noise_c.inputs["Scale"].default_value = log_uniform(20, 40)
    fc_c = _build_float_curve(nt, _noise_fac_output(noise_c), [(0, 0.0), (1, 0.8)])
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{
        "Base Color": color,
        "Coat Weight": 1.0,
        "Specular IOR Level": 1.0,
        "Subsurface Weight": float(np.random.uniform(0.02, 0.05)),
    })
    nt.links.new(fc_r.outputs["Value"], bsdf.inputs["Roughness"])
    if "Coat Roughness" in bsdf.inputs:
        nt.links.new(fc_c.outputs["Value"], bsdf.inputs["Coat Roughness"])
    noise_d = nt.nodes.new("ShaderNodeTexNoise")
    noise_d.inputs["Scale"].default_value = log_uniform(20, 40)
    mul_d = _math(nt, "MULTIPLY", _noise_fac_output(noise_d), log_uniform(0.001, 0.005))
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_d.outputs[0], disp.inputs["Height"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


def make_glass(name="Glass"):
    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfGlass")
    bsdf.inputs["Roughness"].default_value = 0.02
    bsdf.inputs["IOR"].default_value = 1.5
    _connect_output(nt, bsdf)
    return mat


def make_glass_volume(name="GlassVolume"):
    mat = _new_material(name)
    nt = mat.node_tree
    if np.random.uniform() < 0.3:
        color = (1, 1, 1, 1)
    else:
        color = hsv2rgba((np.random.uniform(0, 1),
                          np.random.uniform(0.5, 0.9),
                          np.random.uniform(0.6, 0.9)))
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=0.0, **{"Transmission Weight": 1.0})
    vol = nt.nodes.new("ShaderNodeVolumeAbsorption")
    vol.inputs["Color"].default_value = color
    vol.inputs["Density"].default_value = 100.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    nt.links.new(vol.outputs[0], out.inputs["Volume"])
    return mat


def make_vase_ceramic(name="VaseCeramic"):
    mat = _new_material(name)
    nt = mat.node_tree
    color = hsv2rgba((np.random.uniform(0, 1),
                      np.random.uniform(0, 0.75),
                      np.random.uniform(0, 0.3)))
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{
        "Base Color": color,
        "Subsurface Weight": 0.3,
        "Specular IOR Level": 0.2,
        "Roughness": 0.05,
        "Coat Weight": 0.5,
        "Coat Roughness": 0.05,
        "IOR": 1.47,
    })
    _connect_output(nt, bsdf)
    return mat


def make_colored_glass(name="ColoredGlass"):
    mat = _new_material(name)
    nt = mat.node_tree
    color = hsv2rgba((np.random.uniform(0, 1),
                      np.random.uniform(0, 0.2), 1.0))
    bsdf = nt.nodes.new("ShaderNodeBsdfGlass")
    bsdf.inputs["Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = float(np.random.uniform(0.05, 0.2))
    _connect_output(nt, bsdf)
    return mat


def make_marble(name="Marble"):
    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    scale_v = nt.nodes.new("ShaderNodeVectorMath")
    scale_v.operation = "SCALE"
    ln(tex_coord.outputs["Object"], scale_v.inputs[0])
    rotate = nt.nodes.new("ShaderNodeVectorRotate")
    rotate.rotation_type = "EULER_XYZ"
    ln(scale_v.outputs["Vector"], rotate.inputs["Vector"])
    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    try:
        noise1.noise_dimensions = "4D"
    except (TypeError, AttributeError):
        pass
    noise1.inputs["Scale"].default_value = 3.0
    if "Detail" in noise1.inputs:
        noise1.inputs["Detail"].default_value = 15.0
    ln(rotate.outputs["Vector"], noise1.inputs["Vector"])
    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    noise2.inputs["Scale"].default_value = 8.0
    if "Detail" in noise2.inputs:
        noise2.inputs["Detail"].default_value = 15.0
    ln(_noise_fac_output(noise1), noise2.inputs["Vector"])
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    try:
        vor.feature = "DISTANCE_TO_EDGE"
        vor.voronoi_dimensions = "4D"
    except (TypeError, AttributeError):
        pass
    vor.inputs["Scale"].default_value = 3.0
    if "W" in vor.inputs:
        vor.inputs["W"].default_value = 1.64
    ln(_noise_fac_output(noise2), vor.inputs["Vector"])
    cr1 = _color_ramp(nt, vor.outputs.get("Distance") or vor.outputs[0],
                       [(0.0, (1, 1, 1, 1)), (0.03, (0, 0, 0, 1))])
    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    mix.inputs[0].default_value = 0.8
    ln(_noise_fac_output(noise1), mix.inputs[6])
    mix.inputs[7].default_value = (0.0376, 0.0179, 0.0033, 1.0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Specular IOR Level": 0.6, "Roughness": 0.1})
    ln(mix.outputs[2], bsdf.inputs["Base Color"])
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.02
    ln(cr1.outputs["Color"], disp.inputs["Height"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


def make_metal_basic(name="MetalBasic", color_hsv=None):
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(np.random.uniform(10, 25))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    fc = _build_float_curve(
        nt, _noise_fac_output(noise),
        [(0, float(np.random.uniform(0, 0.2))),
         (1, float(np.random.uniform(0.4, 0.7)))],
    )
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf,
                    Metallic=1.0,
                    **{"Specular IOR Level": float(np.random.uniform(0.5, 1.0))},
                    **{"Base Color": hsv2rgba(color_hsv or metal_hsv())})
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat


def make_brushed_metal(name="BrushedMetal", base_color_hsv=None):
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    mapping_1.inputs["Scale"].default_value = (0.2, 0.2, 5.0)
    ln(tex_coord.outputs["Object"], mapping_1.inputs["Vector"])
    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    try:
        noise2.noise_dimensions = "4D"
    except (TypeError, AttributeError):
        pass
    noise2.inputs["Scale"].default_value = 100.0
    if "Detail" in noise2.inputs:
        noise2.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise2.inputs:
        noise2.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise2.inputs:
        noise2.inputs["Distortion"].default_value = 0.1
    if "W" in noise2.inputs:
        noise2.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    ln(mapping_1.outputs["Vector"], noise2.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[1].default_value = 0.4
    mr.inputs[2].default_value = 0.6
    mr.inputs[3].default_value = 0.8
    mr.inputs[4].default_value = 1.2
    ln(_noise_fac_output(noise2), mr.inputs[0])
    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Color"].default_value = hsv2rgba(base_color_hsv)
    ln(mr.outputs["Result"], hsv_node.inputs["Value"])
    mr_r = nt.nodes.new("ShaderNodeMapRange")
    mr_r.inputs[1].default_value = 0.4
    mr_r.inputs[2].default_value = 0.6
    mr_r.inputs[3].default_value = 0.2
    mr_r.inputs[4].default_value = 0.3
    ln(_noise_fac_output(noise2), mr_r.inputs[0])
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})
    ln(hsv_node.outputs["Color"], bsdf.inputs["Base Color"])
    ln(mr_r.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat


def make_galvanized_metal(name="GalvanizedMetal", base_color_hsv=None):
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    seed_val = float(np.random.uniform(-1000, 1000))
    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    try:
        noise.noise_dimensions = "4D"
    except (TypeError, AttributeError):
        pass
    noise.inputs["Scale"].default_value = 5.0
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise.inputs:
        noise.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 0.2
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = seed_val
    ln(tex_coord.outputs["Object"], noise.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    if hasattr(mix, "clamp_factor"):
        mix.clamp_factor = False
    mix.inputs[0].default_value = 0.05
    ln(tex_coord.outputs["Object"], mix.inputs[6])
    ln(noise.outputs.get("Color") or noise.outputs[1], mix.inputs[7])
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    try:
        vor.distance = "MINKOWSKI"
        vor.voronoi_dimensions = "4D"
    except (TypeError, AttributeError):
        pass
    vor.inputs["Scale"].default_value = 500.0
    if "W" in vor.inputs:
        vor.inputs["W"].default_value = seed_val
    ln(mix.outputs[2], vor.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    ln(vor.outputs.get("Color") or vor.outputs[0], mr.inputs[0])
    mr.inputs[3].default_value = 0.1
    mr.inputs[4].default_value = 0.5
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf,
                    Metallic=1.0,
                    **{"Specular IOR Level": 0.0,
                       "Base Color": hsv2rgba(base_color_hsv)})
    ln(mr.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat


def make_hammered_metal(name="HammeredMetal", base_color_hsv=None):
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    seed_val = float(np.random.uniform(-1000, 1000))
    scale_val = log_uniform(0.8, 1.2)
    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    try:
        noise.noise_dimensions = "4D"
    except (TypeError, AttributeError):
        pass
    noise.inputs["Scale"].default_value = scale_val * 20.0
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise.inputs:
        noise.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 0.2
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = seed_val
    ln(tex_coord.outputs["Object"], noise.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    if hasattr(mix, "clamp_factor"):
        mix.clamp_factor = False
    mix.inputs[0].default_value = 0.01
    ln(tex_coord.outputs["Object"], mix.inputs[6])
    ln(noise.outputs.get("Color") or noise.outputs[1], mix.inputs[7])
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    try:
        vor.voronoi_dimensions = "4D"
        vor.feature = "SMOOTH_F1"
    except (TypeError, AttributeError):
        pass
    vor.inputs["Scale"].default_value = scale_val * 300.0
    if "Smoothness" in vor.inputs:
        vor.inputs["Smoothness"].default_value = 0.2
    if "W" in vor.inputs:
        vor.inputs["W"].default_value = seed_val
    ln(mix.outputs[2], vor.inputs["Vector"])
    mul1 = _math(nt, "MULTIPLY", vor.outputs.get("Distance") or vor.outputs[0], scale_val)
    pow1 = _math(nt, "POWER", mul1.outputs[0], 2.5)
    mul2 = _math(nt, "MULTIPLY", pow1.outputs[0], log_uniform(0.001, 0.003))
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf,
                    Metallic=1.0,
                    **{"Specular IOR Level": 0.0, "Roughness": 0.1,
                       "Base Color": hsv2rgba(base_color_hsv)})
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    ln(mul2.outputs[0], disp.inputs["Height"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


def make_grained_metal(name="GrainedMetal", base_color_hsv=None):
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    roughness_param = float(np.random.uniform(0.0, 1.0))
    seed_val = float(np.random.uniform(-1000, 1000))
    scale_param = 1.0
    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[0].default_value = roughness_param
    mr.inputs[3].default_value = 0.05
    mr.inputs[4].default_value = 0.25
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf,
                    Metallic=1.0,
                    **{"Specular IOR Level": 0.0,
                       "Base Color": hsv2rgba(base_color_hsv)})
    ln(mr.outputs["Result"], bsdf.inputs["Roughness"])
    mul_scale = _math(nt, "MULTIPLY", scale_param * 2000.0, None)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    try:
        noise.noise_dimensions = "4D"
    except (TypeError, AttributeError):
        pass
    noise.inputs["Scale"].default_value = scale_param * 2000.0
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = seed_val
    ln(tex_coord.outputs["Object"], noise.inputs["Vector"])
    mul1 = _math(nt, "MULTIPLY", mr.outputs["Result"], 0.4)
    mul2 = _math(nt, "MULTIPLY", _noise_fac_output(noise), mul1.outputs[0])
    mul3 = _math(nt, "MULTIPLY", mul2.outputs[0], 0.010)
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    ln(mul3.outputs[0], disp.inputs["Height"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


def make_plastic_rough(name="PlasticRough"):
    roughness = float(np.random.uniform(0, 1))
    seed_val = float(np.random.uniform(-1000, 1000))
    base_color = hsv2rgba((np.random.uniform(0, 1),
                           np.random.uniform(0.5, 0.8),
                           log_uniform(0.01, 0.5)))
    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[0].default_value = roughness
    mr.inputs[3].default_value = 0.05
    mr.inputs[4].default_value = 0.25
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Base Color": base_color})
    ln(mr.outputs["Result"], bsdf.inputs["Roughness"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    try:
        noise.noise_dimensions = "4D"
    except (TypeError, AttributeError):
        pass
    noise.inputs["Scale"].default_value = 2000.0
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = seed_val
    ln(tex_coord.outputs["Object"], noise.inputs["Vector"])
    rough_mapped = mr.outputs["Result"]
    mul1 = _math(nt, "MULTIPLY", rough_mapped, 0.4)
    mul2 = _math(nt, "MULTIPLY", _noise_fac_output(noise), mul1.outputs[0])
    mul3 = _math(nt, "MULTIPLY", mul2.outputs[0], 0.003)
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    ln(mul3.outputs[0], disp.inputs["Height"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


def make_plastic_translucent(name="PlasticTranslucent"):
    base_color = hsv2rgba((np.random.uniform(0, 1),
                           np.random.uniform(0.5, 0.8),
                           log_uniform(0.4, 0.8)))
    blend = float(np.random.uniform(0.2, 0.4))
    ior = float(np.random.uniform(1.2, 1.6))
    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = blend
    glass = nt.nodes.new("ShaderNodeBsdfGlass")
    glass.inputs["Color"].default_value = base_color
    glass.inputs["Roughness"].default_value = 0.2
    glass.inputs["IOR"].default_value = ior
    glossy = nt.nodes.new("ShaderNodeBsdfGlossy")
    glossy.inputs["Roughness"].default_value = 0.2
    mix_sh = nt.nodes.new("ShaderNodeMixShader")
    ln(lw.outputs["Fresnel"], mix_sh.inputs["Fac"])
    ln(glass.outputs[0], mix_sh.inputs[1])
    ln(glossy.outputs[0], mix_sh.inputs[2])
    _connect_output(nt, mix_sh)
    return mat


def make_plastic(name="Plastic"):
    is_rough = float(np.random.uniform(0, 1))
    is_translucent = float(np.random.uniform(0, 1))
    if is_rough > is_translucent:
        return make_plastic_rough(name)
    else:
        return make_plastic_translucent(name)


def make_wood(name="Wood"):
    """
    Uses noise-based fake wood grain since MusgraveTexture removed in Blender 5.0."""

    color = hsv2rgba(bark_hsv())
    w = float(np.random.uniform(0, 1))
    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (5.0, 100.0, 100.0)
    ln(tex_coord.outputs["Object"], mapping.inputs["Vector"])
    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    try:
        noise1.noise_dimensions = "4D"
    except (TypeError, AttributeError):
        pass
    noise1.inputs["Scale"].default_value = 10.0
    if "Detail" in noise1.inputs:
        noise1.inputs["Detail"].default_value = 15.0
    if "W" in noise1.inputs:
        noise1.inputs["W"].default_value = w
    ln(mapping.outputs["Vector"], noise1.inputs["Vector"])
    cr1 = _color_ramp(nt, _noise_fac_output(noise1),
                       [(0.3, color), (0.7, (0.02, 0.01, 0.005, 1.0))])
    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    noise2.inputs["Scale"].default_value = 2.0
    if "Detail" in noise2.inputs:
        noise2.inputs["Detail"].default_value = 5.0
    ln(tex_coord.outputs["Object"], noise2.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    mix.inputs[0].default_value = 0.3
    ln(cr1.outputs["Color"], mix.inputs[6])
    ln(_noise_fac_output(noise2), mix.inputs[7])
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=0.4, **{"Specular IOR Level": 0.3})
    ln(mix.outputs[2], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf)
    return mat



CUP_REGISTRY = [
    # decorative_hard = decorative_metal + ceramics
    (make_brushed_metal, 1.0),
    (make_galvanized_metal, 1.0),
    (make_grained_metal, 1.0),
    (make_hammered_metal, 1.0),
    (make_vase_ceramic, 4.0),
    (make_colored_glass, 2.0),
    (make_marble, 1.0),
    (make_glass_volume, 2.0),
    (make_ceramic, 1.0),
    # additional cup entries
    (make_metal_basic, 2.0),
    (make_plastic, 5.0),
    (make_plastic_translucent, 5.0),
    (make_glass, 3.0),
]

WOODS_REGISTRY = [
    (make_wood, 1.0),
]


def get_blade_material(name="BladeSurface"):
    ctor = weighted_sample_mat(CUP_REGISTRY)
    return ctor(name=name)


def get_handle_material(name="HandleSurface"):
    ctor = weighted_sample_mat(WOODS_REGISTRY)
    return ctor(name=name)


# --- wear_tear -------------------------------------------------------------

WEAR_TEAR_PROB = [0.5, 0.5]
SCRATCH_LABEL = "scratch"
EDGE_WEAR_LABEL = "wear_tear"


def get_scratch_params():
    return dict(
        angle1=float(np.random.uniform(10.0, 80.0)),
        angle2=float(np.random.uniform(-80.0, -10.0)),
        scratch_scale=log_uniform(5, 80),
        scratch_mask_ratio=log_uniform(0.01, 0.9),
        scratch_mask_noise=log_uniform(5, 40),
        scratch_depth=log_uniform(0.1, 1.0),
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
    try:
        map1.vector_type = "TEXTURE"
    except (TypeError, AttributeError):
        pass
    map1.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map1.inputs["Vector"])
    nt.links.new(cxyz1.outputs[0], map1.inputs["Rotation"])
    noise1 = _noise_tex(nt, map1.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)
    cxyz2 = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(n_angle2.outputs[0], cxyz2.inputs["Y"])
    map2 = nt.nodes.new("ShaderNodeMapping")
    try:
        map2.vector_type = "TEXTURE"
    except (TypeError, AttributeError):
        pass
    map2.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map2.inputs["Vector"])
    nt.links.new(cxyz2.outputs[0], map2.inputs["Rotation"])
    noise2 = _noise_tex(nt, map2.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)
    add = _math(nt, "ADD", _noise_fac_output(noise1), _noise_fac_output(noise2))
    map3 = nt.nodes.new("ShaderNodeMapping")
    try:
        map3.vector_type = "TEXTURE"
    except (TypeError, AttributeError):
        pass
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


def _build_edge_wear_graph(nt, original_bsdf_node, original_displacement_node, p):
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
    noise_a = _noise_tex(nt, mapping.outputs["Vector"],
                         n_scratch_mask_randomness.outputs[0], detail=1.0)
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
    noise_b = _noise_tex(nt, mapping.outputs["Vector"],
                         n_worn_mask_randomness.outputs[0], detail=1.0)
    cr_c = _color_ramp(nt, _noise_fac_output(noise_b),
                       [(0.0764, (1, 1, 1, 1)), (0.5709, (0, 0, 0, 1))])
    mul_b = _math(nt, "MULTIPLY", abs_b.outputs[0], cr_c.outputs["Color"], clamp=True)
    mul_b1 = _math(nt, "MULTIPLY", n_worn_opacity.outputs[0], mul_b.outputs[0], clamp=True)
    cr_d = _color_ramp(nt, mul_b1.outputs[0],
                       [(0.0, (0, 0, 0, 1)), (0.7782, (1, 1, 1, 1))])
    combine_color = nt.nodes.new("ShaderNodeCombineColor")
    try:
        combine_color.mode = "HSV"
    except (TypeError, AttributeError):
        pass
    nt.links.new(n_edge_hue.outputs[0], combine_color.inputs["Red"])
    combine_color.inputs["Green"].default_value = 0.7733
    combine_color.inputs["Blue"].default_value = 0.0100
    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
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
    try:
        vor_h.feature = "DISTANCE_TO_EDGE"
    except (TypeError, AttributeError):
        pass
    nt.links.new(map_h.outputs["Vector"], vor_h.inputs["Vector"])
    nt.links.new(n_scratch_density.outputs[0], vor_h.inputs["Scale"])
    map_v = nt.nodes.new("ShaderNodeMapping")
    map_v.inputs["Scale"].default_value = (1.0, 10.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map_v.inputs["Vector"])
    scale_v = _vmath(nt, "SCALE", in0=n_scratch_density.outputs[0], scale=2.0)
    vor_v = nt.nodes.new("ShaderNodeTexVoronoi")
    try:
        vor_v.feature = "DISTANCE_TO_EDGE"
    except (TypeError, AttributeError):
        pass
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
# === Geometry helpers (copied verbatim from objects_blender/tableware/KnifeFactory.py)
# ============================================================================

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    bpy.context.scene.cursor.location = (0, 0, 0)


def select_only(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def apply_transform(obj, loc=False):
    select_only(obj)
    bpy.ops.object.transform_apply(location=loc, rotation=True, scale=True)


def modify_mesh(obj, mod_type, apply=True, **kwargs):
    select_only(obj)
    mod = obj.modifiers.new(name=mod_type, type=mod_type)
    for k, v in kwargs.items():
        setattr(mod, k, v)
    if apply:
        bpy.ops.object.modifier_apply(modifier=mod.name)


def write_co(obj, arr):
    obj.data.vertices.foreach_set('co', arr.reshape(-1))


def subsurf(obj, levels, simple=False):
    if levels > 0:
        modify_mesh(obj, 'SUBSURF',
                     levels=levels, render_levels=levels,
                     subdivision_type='SIMPLE' if simple else 'CATMULL_CLARK')


def new_grid(x_subdivisions=10, y_subdivisions=10):
    bpy.ops.mesh.primitive_grid_add(
        location=(0, 0, 0),
        x_subdivisions=x_subdivisions,
        y_subdivisions=y_subdivisions
    )
    obj = bpy.context.active_object
    apply_transform(obj, loc=True)
    return obj


# ============================================================================
# === SpatulaFactory geometry (verbatim from objects_blender/) ===============
# ============================================================================


def add_guard_extrude(obj, guard_threshold, guard_depth, guard_type):
    """

    Extrudes handle faces by guard_depth and stores a 'guard' boolean face attribute.
    guard_threshold: faces with x < guard_threshold are selected as handle.
    guard_type: 'round' or 'double'. 'double' additionally filters by |normal.z| > 0.8.
    """

    ng = bpy.data.node_groups.new("GuardExtrude", 'GeometryNodeTree')

    # Interface sockets
    in_sock = ng.interface.new_socket('Geometry', in_out='INPUT',
                                       socket_type='NodeSocketGeometry')
    out_sock = ng.interface.new_socket('Geometry', in_out='OUTPUT',
                                        socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    group_in = nodes.new('NodeGroupInput')
    group_out = nodes.new('NodeGroupOutput')

    # Position → Separate XYZ → x
    pos = nodes.new('GeometryNodeInputPosition')
    sep = nodes.new('ShaderNodeSeparateXYZ')
    links.new(pos.outputs['Position'], sep.inputs['Vector'])

    # x < guard_threshold
    compare_x = nodes.new('FunctionNodeCompare')
    compare_x.data_type = 'FLOAT'
    compare_x.operation = 'LESS_THAN'
    links.new(sep.outputs['X'], compare_x.inputs[0])  # A
    compare_x.inputs[1].default_value = guard_threshold  # B

    if guard_type == "double":
        # Also filter: |normal.z| > 0.8
        normal = nodes.new('GeometryNodeInputNormal')
        sep_n = nodes.new('ShaderNodeSeparateXYZ')
        links.new(normal.outputs['Normal'], sep_n.inputs['Vector'])
        abs_nz = nodes.new('ShaderNodeMath')
        abs_nz.operation = 'ABSOLUTE'
        links.new(sep_n.outputs['Z'], abs_nz.inputs[0])
        compare_nz = nodes.new('FunctionNodeCompare')
        compare_nz.data_type = 'FLOAT'
        compare_nz.operation = 'GREATER_THAN'
        links.new(abs_nz.outputs[0], compare_nz.inputs[0])
        compare_nz.inputs[1].default_value = 0.8
        bool_and = nodes.new('FunctionNodeBooleanMath')
        bool_and.operation = 'AND'
        links.new(compare_x.outputs['Result'], bool_and.inputs[0])
        links.new(compare_nz.outputs['Result'], bool_and.inputs[1])
        selection_out = bool_and.outputs[0]
    else:
        selection_out = compare_x.outputs['Result']

    # Extrude Mesh
    extrude = nodes.new('GeometryNodeExtrudeMesh')
    links.new(group_in.outputs['Geometry'], extrude.inputs['Mesh'])
    links.new(selection_out, extrude.inputs['Selection'])
    extrude.inputs['Offset Scale'].default_value = guard_depth
    extrude.inputs['Individual'].default_value = False

    # guard = top OR side
    top_out = extrude.outputs['Top']
    side_out = extrude.outputs['Side']
    bool_or = nodes.new('FunctionNodeBooleanMath')
    bool_or.operation = 'OR'
    links.new(top_out, bool_or.inputs[0])
    links.new(side_out, bool_or.inputs[1])

    # Store Named Attribute "guard" (BOOLEAN on FACE domain)
    store = nodes.new('GeometryNodeStoreNamedAttribute')
    store.data_type = 'BOOLEAN'
    store.domain = 'FACE'
    links.new(extrude.outputs['Mesh'], store.inputs['Geometry'])
    # Find the Name input
    for inp in store.inputs:
        if inp.name == 'Name':
            inp.default_value = "guard"
            break
    # Find the Value input (boolean)
    for inp in store.inputs:
        if inp.name == 'Value' and inp.type == 'BOOLEAN':
            links.new(bool_or.outputs[0], inp)
            break

    links.new(store.outputs['Geometry'], group_out.inputs['Geometry'])

    # Apply as modifier
    mod = obj.modifiers.new("GuardExtrude", 'NODES')
    mod.node_group = ng
    select_only(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)


def create_spatula(seed):
    """Create spatula geometry with materials assigned.

    Returns the final object with up to 2 material slots:
      slot 0 = spatula surface (from cup registry — typically metal)
      slot 1 = handle/guard surface (from woods registry — only if has_guard)

    Geometry is verbatim from objects_blender/tableware/SpatulaFactory.py,
    (ForkFactory subclass with has_cut=False, wider y_length, shallower z_depth).
    """
    # --- Materials (sampled under separate seed to avoid RNG coupling) ---
    mat_seed = ((seed + 7) * 2654435761) & 0xFFFFFFFF
    np.random.seed(mat_seed)
    random.seed(mat_seed)

    surface_mat = get_blade_material("SpatulaSurface")
    handle_mat = get_handle_material("HandleSurface")

    scratch_prob, edge_wear_prob = WEAR_TEAR_PROB
    do_scratch = uniform() <= scratch_prob
    do_edge_wear = uniform() <= edge_wear_prob
    scratch_params = get_scratch_params() if do_scratch else None
    edge_wear_params = get_edge_wear_params() if do_edge_wear else None

    # --- Geometry RNG (verbatim draw order from objects_blender/tableware/SpatulaFactory.py) ---
    np.random.seed(seed)
    random.seed(seed)

    x_end = 0.15
    x_length = float(log_uniform(0.4, 0.8))
    x_tip = uniform(0.15, 0.2)
    # Spatula overrides: wider, shallower
    y_length = float(log_uniform(0.08, 0.12))
    z_depth = uniform(0, 0.05)
    z_offset = uniform(0.0, 0.05)
    thickness = float(log_uniform(0.008, 0.015))
    n_cuts = np.random.randint(1, 3) if uniform(0, 1) < 0.3 else 3
    scale = float(log_uniform(0.15, 0.25))

    # --- Build geometry (verbatim from objects_blender/tableware/SpatulaFactory.py) ---
    x_anchors = np.array([
        x_tip,
        uniform(-0.04, -0.02),
        -0.08,
        -0.12,
        -x_end,
        -x_end - x_length,
        -x_end - x_length * float(log_uniform(1.2, 1.4)),
    ])
    y_anchors = np.array([
        y_length * float(log_uniform(0.8, 1.0)),
        y_length * float(log_uniform(1.0, 1.2)),
        y_length * float(log_uniform(0.6, 1.0)),
        y_length * float(log_uniform(0.2, 0.4)),
        float(log_uniform(0.01, 0.02)),
        float(log_uniform(0.02, 0.05)),
        float(log_uniform(0.01, 0.02)),
    ])
    z_anchors = np.array([
        0,
        -z_depth,
        -z_depth,
        0,
        z_offset,
        z_offset + uniform(-0.02, 0.04),
        z_offset + uniform(-0.02, 0),
    ])

    # Sample has_guard/guard_type/guard_depth AFTER all geometry params to avoid
    # shifting the RNG sequence. Save/restore so these draws do not affect geometry.
    _rng_state = np.random.get_state()
    has_guard = uniform(0, 1) < 0.4
    guard_type = "round" if uniform(0, 1) < 0.6 else "double"
    guard_depth = float(log_uniform(0.2, 1.0)) * thickness
    np.random.set_state(_rng_state)

    n = 2 * (n_cuts + 1)
    obj = new_grid(x_subdivisions=len(x_anchors) - 1, y_subdivisions=n - 1)
    x = np.concatenate([x_anchors] * n)
    y = np.ravel(y_anchors[np.newaxis, :] * np.linspace(1, -1, n)[:, np.newaxis])
    z = np.concatenate([z_anchors] * n)
    write_co(obj, np.stack([x, y, z], -1))
    # No cuts for spatula (has_cut = False)
    modify_mesh(obj, 'SOLIDIFY', thickness=thickness)
    subsurf(obj, 1)

    # Selection: x < -x_end, matching fork.py:ForkFactory.create_asset.
    # guard_depth is applied even when has_guard is False, but then the guard
    # behavior: finalize_assets only assigns guard_surface when has_guard). ---
    guard_threshold = -x_end
    if has_guard:
        add_guard_extrude(obj, guard_threshold, guard_depth, guard_type)

    subsurf(obj, 1)
    obj.scale = [scale] * 3
    apply_transform(obj)

    # --- Assign materials ---
    # Slot 0: spatula surface (entire mesh default)
    obj.data.materials.append(surface_mat)

    if has_guard:
        # Slot 1: handle/guard surface (only when has_guard, mirrors
        # finalize_assets conditional in TablewareFactory)
        obj.data.materials.append(handle_mat)

        # Mark guard faces with material_index=1 using the stored "guard" attribute
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()

        guard_layer = None
        for layer_name in bm.faces.layers.int.keys():
            if layer_name == "guard":
                guard_layer = bm.faces.layers.int["guard"]
                break

        if guard_layer is not None:
            for face in bm.faces:
                if face[guard_layer]:
                    face.material_index = 1
        else:
            # Fallback: use the "guard" attribute from mesh domain
            mesh = obj.data
            if "guard" in mesh.attributes:
                attr = mesh.attributes["guard"]
                if attr.domain == 'FACE':
                    guard_vals = np.zeros(len(mesh.polygons), dtype=bool)
                    attr.data.foreach_get("value", guard_vals)
                    for i, face in enumerate(bm.faces):
                        if guard_vals[i]:
                            face.material_index = 1

        bm.to_mesh(obj.data)
        bm.free()

    # --- Apply wear_tear ---
    if do_scratch and scratch_params:
        apply_scratches(obj, **scratch_params)
    if do_edge_wear and edge_wear_params:
        apply_edge_wear(obj, **edge_wear_params)

    obj.name = "SpatulaFactory"
    return obj


# ============================================================================
# === Entry point ============================================================
# ============================================================================

clear_scene()
spatula = create_spatula(SEED)
print(f"SpatulaFactory: seed={SEED}, verts={len(spatula.data.vertices)}, "
      f"material_slots={len(spatula.data.materials)}")
