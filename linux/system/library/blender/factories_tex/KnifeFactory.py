# [FL_INDEX: keywords="blender_factory, procedural_3d, KnifeFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: KnifeFactory | Category: factories_tex
# Prompt: A 3D model of a table knife rendered from a slightly elevated top-down perspective. The knife features a long, flat blade that is wide at the base and tapers to a pointed tip, a smooth continuous handle that blends into the blade, and a uniform dark blue-gray coloring across the entire piece.

# KnifeFactory -- textured conversion
#
# Geometry copied verbatim from:
#   objects_blender/tableware/KnifeFactory.py
# Guard extrusion logic from:
# Shaders translated faithfully from:
#
# Knife material binding model:
#   self.surface from material_assignments.cup (decorative_hard + MetalBasic +
#   Plastic + PlasticTranslucent + Glass) for the blade,
#   self.guard_surface from material_assignments.woods for the handle,
#   plus wear_tear (50%/50%).
#   finalize_assets() assigns surface to entire mesh, guard_surface to "guard"
#   selection (handle region).

import os
import bpy
import bmesh
import math
import random
import colorsys
import numpy as np
from numpy.random import uniform

# --- Seed ---

SEED = int(os.environ.get("SEED", 0))

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)

def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def log_uniform(lo, hi, size=None):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi), size)))

def metal_hsv():
    """py:metal_hsv."""

    if np.random.uniform() < 0.2:
        return (np.random.uniform(0, 1),
                np.random.uniform(0.0, 0.2),
                log_uniform(0.05, 0.3))
    return (np.random.uniform(0, 1),
            np.random.uniform(0.3, 0.6),
            log_uniform(0.02, 0.5))

def bark_hsv():
    """py:bark_hsv."""

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
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.02
    bsdf.inputs["IOR"].default_value = 1.5
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = 1.0
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = 1.0
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
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
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
    glass = nt.nodes.new("ShaderNodeBsdfPrincipled")
    glass.inputs["Base Color"].default_value = base_color
    glass.inputs["Roughness"].default_value = 0.2
    glass.inputs["IOR"].default_value = ior
    if "Transmission Weight" in glass.inputs:
        glass.inputs["Transmission Weight"].default_value = 1.0
    elif "Transmission" in glass.inputs:
        glass.inputs["Transmission"].default_value = 1.0
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
#     Uses noise-based fake wood grain since MusgraveTexture removed in Blender 5.0."""

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

# --- Geometry helpers (copied verbatim from objects_blender/tableware/KnifeFactory.py)

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

def read_co(obj):
    arr = np.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get('co', arr)
    return arr.reshape(-1, 3)

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

# --- KnifeFactory geometry (verbatim from objects_blender/) ---

def make_knife_tip(obj, y_offset, y_length):
    select_only(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    for e in bm.edges:
        u, v = e.verts
        x0, y0, z0 = u.co
        x1, y1, z1 = v.co
        if x0 >= 0 and x1 >= 0 and abs(x0 - x1) < 2e-4:
            if y0 > y_offset * y_length and y1 > y_offset * y_length:
                bmesh.ops.pointmerge(bm, verts=[u, v], merge_co=(u.co + v.co) / 2)
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_loose(extend=False)
    bpy.ops.mesh.delete(type='EDGE')
    bpy.ops.object.mode_set(mode='OBJECT')

def add_guard_extrude(obj, guard_threshold, guard_depth, guard_type):
    """Replicate TablewareFactory.add_guard using GeoNodes.

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

    # Position -> Separate XYZ -> x
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

def create_knife(seed):
    """Create knife geometry with materials assigned.

    Returns the final object with 2 material slots:
      slot 0 = blade surface (from cup registry)
      slot 1 = handle/guard surface (from woods registry)
    """
    # --- RNG for geometry params (matches __init__) ---
    np.random.seed(seed)
    random.seed(seed)

    """
    """

    x_end = 0.5
    x_length = float(log_uniform(0.4, 0.7))
    has_guard = uniform(0, 1) < 0.7
    if has_guard:
        y_length = float(log_uniform(0.1, 0.5))
        y_guard = y_length * float(log_uniform(0.2, 0.4))
    else:
        y_length = float(log_uniform(0.1, 0.2))
        y_guard = y_length * float(log_uniform(0.3, 0.5))
    x_guard = float(uniform(0, 0.2))
    has_tip = uniform(0, 1) < 0.7
    thickness = float(log_uniform(0.02, 0.03))
    y_off_rand = uniform(0, 1)
    y_offset = 0.2 if y_off_rand < 1/8 else 0.5 if y_off_rand < 1/4 else uniform(0.2, 0.6)
    guard_type = "round" if uniform(0, 1) < 0.6 else "double"
    guard_depth = float(log_uniform(0.2, 1.0)) * thickness
    scale = float(log_uniform(0.2, 0.3))

    # --- Materials (sampled under separate seed) ---
    mat_seed = ((seed + 7) * 2654435761) & 0xFFFFFFFF
    np.random.seed(mat_seed)
    random.seed(mat_seed)

    blade_mat = get_blade_material("BladeSurface")
    handle_mat = get_handle_material("HandleSurface")

    scratch_prob, edge_wear_prob = WEAR_TEAR_PROB
    do_scratch = uniform() <= scratch_prob
    do_edge_wear = uniform() <= edge_wear_prob
    scratch_params = get_scratch_params() if do_scratch else None
    edge_wear_params = get_edge_wear_params() if do_edge_wear else None

    # --- Restore geometry RNG to create_asset position ---
    # The code seeds __init__ with factory_seed, then create_asset runs
    # with the global RNG. We re-seed here and skip __init__ draws to align.
    np.random.seed(seed)
    random.seed(seed)
    # Skip __init__ draws to align with create_asset RNG state:
    _ = log_uniform(0.4, 0.7)       # x_length
    _hg = uniform(0, 1)             # has_guard check
    if _hg < 0.7:
        _ = log_uniform(0.1, 0.5)   # y_length
        _ = log_uniform(0.2, 0.4)   # y_guard ratio
    else:
        _ = log_uniform(0.1, 0.2)
        _ = log_uniform(0.3, 0.5)
    _ = uniform(0, 0.2)             # x_guard
    _ = uniform(0, 1)               # has_tip check
    _ = log_uniform(0.02, 0.03)     # thickness
    _ = uniform(0, 1)               # y_off_rand
    if _ >= 1/4:
        _ = uniform(0.2, 0.6)       # y_offset conditional
    _ = uniform(0, 1)               # guard_type check
    _ = log_uniform(0.2, 1.0)       # guard_depth ratio
    _ = log_uniform(0.2, 0.3)       # scale
    # Now RNG is at create_asset position

    # --- Build geometry (matches KnifeFactory.create_asset) ---
    x_anchors = np.array([
        x_end,
        uniform(0.5, 0.8) * x_end,
        uniform(0.3, 0.4) * x_end,
        1e-3,
        0,
        -1e-3,
        -2e-3,
        -x_end * x_length + 1e-3,
        -x_end * x_length,
    ])
    y_anchors = np.array([
        1e-3,
        y_length * float(log_uniform(0.75, 0.95)),
        y_length,
        y_length,
        y_length,
        y_guard,
        y_guard,
        y_guard,
        y_guard,
    ])
    if not has_guard:
        indices = [0, 1, 2, 4, 5, 7, 8]
        x_anchors = x_anchors[indices]
        y_anchors = y_anchors[indices]
    if has_tip:
        indices = [0] + list(range(len(x_anchors)))
        x_anchors = x_anchors[indices]
        x_anchors[0] += 1e-3
        y_anchors = y_anchors[indices]
        y_anchors[1] += 3e-3

    obj = new_grid(x_subdivisions=len(x_anchors) - 1, y_subdivisions=1)
    x = np.concatenate([x_anchors] * 2)
    y = np.concatenate([y_anchors, np.zeros_like(y_anchors)])
    y[0::len(y_anchors)] += y_offset * y_length
    if has_tip:
        y[1::len(y_anchors)] += y_offset * y_length
        y[2::len(y_anchors)] += y_offset * (y_length - y_anchors[2])
    else:
        y[1::len(y_anchors)] += y_offset * (y_length - y_anchors[1])
    z = np.concatenate([np.zeros_like(x_anchors)] * 2)
    write_co(obj, np.stack([x, y, z], -1))
    modify_mesh(obj, 'SOLIDIFY', thickness=thickness)
    make_knife_tip(obj, y_offset, y_length)
    subsurf(obj, 1)

    # --- Guard extrusion (replicates add_guard) ---
    guard_threshold = -x_guard * x_length * x_end
    add_guard_extrude(obj, guard_threshold, guard_depth, guard_type)

    subsurf(obj, 1)
    subsurf(obj, 1, True)
    obj.scale = [scale] * 3
    apply_transform(obj)

    # --- Assign materials ---
    # Slot 0: blade surface (entire mesh default)
    obj.data.materials.append(blade_mat)
    # Slot 1: handle/guard surface
    obj.data.materials.append(handle_mat)

    # Mark guard faces with material_index=1 using the stored "guard" attribute
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    # Try to read the "guard" boolean attribute
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
        # Read from mesh custom attributes
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

    obj.name = "KnifeFactory"
    return obj

# --- Entry point ---

clear_scene()
knife = create_knife(SEED)
print(f"KnifeFactory: seed={SEED}, verts={len(knife.data.vertices)}, "
      f"material_slots={len(knife.data.materials)}")

