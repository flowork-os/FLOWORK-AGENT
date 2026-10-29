# [FL_INDEX: keywords="blender_factory, procedural_3d, PanFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: PanFactory | Category: factories_tex
# Prompt: A 3D model of a frying pan rendered from a three-quarter perspective. The pan features a wide shallow circular cooking surface with low curved sides, a dark blue-gray interior, a dark exterior body, and a long flat handle extending to one side with a light-colored wooden grip section and a small rectangular hole at the end.

"""PanFactory -- standalone textured pan (metal/ceramic/glass/plastic + wood guard).

Shader pool mirrors material_assignments.cup:
  decorative_metal: BrushedMetal(1), GalvanizedMetal(1), GrainedMetal(1), HammeredMetal(0.7)
  + VaseCeramic(4), ColoredGlass(2), Marble(1), GlassVolume(2), Ceramic(1)
  + MetalBasic(2), Plastic(5), PlasticTranslucent(5), Glass(3)

Guard surface (if has_guard ~80%): from material_assignments.woods

No wear-tear: PanFactory explicitly sets self.scratch = self.edge_wear = None.

Geometry: copied from objects_blender/tableware/PanFactory.py (circle rings + bridge +
fill_grid + handle extrude + solidify + subsurf + optional boolean hole).
Guard: extrude faces where x > x_guard by guard_depth, assign wood material.
"""


import os
import math
import random
import colorsys
import hashlib

import bpy
import bmesh
import numpy as np
from numpy.random import uniform

# ---------------------------------------------------------------------------
# SEED handling
# ---------------------------------------------------------------------------
SEED = int(os.environ.get("SEED", 0))

def int_hash(x):
    m = hashlib.md5()
    for s in x:
        m.update(str(s).encode("utf-8"))
    return abs(int(m.hexdigest(), 16)) % (2**32 - 1)

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def log_uniform(lo, hi, size=None):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi), size)))

def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def metal_hsv():
    if np.random.uniform() < 0.2:
        return (np.random.uniform(0, 1),
                np.random.uniform(0.0, 0.2),
                log_uniform(0.05, 0.3))
    return (np.random.uniform(0, 1),
            np.random.uniform(0.3, 0.6),
            log_uniform(0.02, 0.5))

def bark_hsv():
    wood_hex = ["#8b5a2b", "#a0522d", "#cd853f", "#d2691e",
                "#6b4423", "#5d4037", "#7b3f00"]
    h_str = wood_hex[np.random.randint(0, len(wood_hex))].lstrip("#")
    r, g, b = (int(h_str[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return colorsys.rgb_to_hsv(r, g, b)

def weighted_sample(registry):
    classes, weights = zip(*registry)
    weights = np.array(weights, dtype=float)
    return classes[int(np.random.choice(len(classes), p=weights / weights.sum()))]

# ---------------------------------------------------------------------------
# Material helpers
# ---------------------------------------------------------------------------
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
            n.inputs[idx].default_value = float(val)
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

# ---------------------------------------------------------------------------
# Material factories -- inlined translations of shaders
# ---------------------------------------------------------------------------

# --- Ceramic ---------------------------------------------------------------
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

# --- Glass -----------------------------------------------------------------
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

# --- GlassVolume -----------------------------------------------------------
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

# --- VaseCeramic -----------------------------------------------------------
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

# --- ColoredGlass ---------------------------------------------------------
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

# --- Marble ----------------------------------------------------------------
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

# --- MetalBasic ------------------------------------------------------------
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

# --- BrushedMetal ----------------------------------------------------------
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

# --- GalvanizedMetal -------------------------------------------------------
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
    mr_v = nt.nodes.new("ShaderNodeMapRange")
    ln(vor.outputs.get("Color") or vor.outputs[0], mr_v.inputs[0])
    mr_v.inputs[3].default_value = 0.1
    mr_v.inputs[4].default_value = 0.5
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf,
                    Metallic=1.0,
                    **{"Specular IOR Level": 0.0,
                       "Base Color": hsv2rgba(base_color_hsv)})
    ln(mr_v.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

# --- GrainedMetal ----------------------------------------------------------
def make_grained_metal(name="GrainedMetal"):
    mat = _new_material(name)
    nt = mat.node_tree
    base_color = hsv2rgba(metal_hsv())
    roughness = float(np.random.uniform(0.0, 1.0))
    seed_val = float(np.random.uniform(-1000, 1000))
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mr_rough = nt.nodes.new("ShaderNodeMapRange")
    mr_rough.inputs["Value"].default_value = roughness
    mr_rough.inputs[3].default_value = 0.05
    mr_rough.inputs[4].default_value = 0.25
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = base_color
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})
    nt.links.new(mr_rough.outputs["Result"], bsdf.inputs["Roughness"])
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
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    mul1 = _math(nt, "MULTIPLY", mr_rough.outputs["Result"], 0.4)
    mul2 = _math(nt, "MULTIPLY", _noise_fac_output(noise), mul1.outputs[0])
    mul3 = _math(nt, "MULTIPLY", mul2.outputs[0], 0.01)
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul3.outputs[0], disp.inputs["Height"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# --- HammeredMetal ---------------------------------------------------------
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

# --- PlasticRough ----------------------------------------------------------
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
    mul1 = _math(nt, "MULTIPLY", mr.outputs["Result"], 0.4)
    mul2 = _math(nt, "MULTIPLY", _noise_fac_output(noise), mul1.outputs[0])
    mul3 = _math(nt, "MULTIPLY", mul2.outputs[0], 0.003)
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    ln(mul3.outputs[0], disp.inputs["Height"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# --- PlasticTranslucent ---------------------------------------------------
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

# --- Plastic ---------------------------------------------------------------
def make_plastic(name="Plastic"):
    is_rough = float(np.random.uniform(0, 1))
    is_translucent = float(np.random.uniform(0, 1))
    if is_rough > is_translucent:
        return make_plastic_rough(name)
    else:
        return make_plastic_translucent(name)

# --- Wood (for guard) -----------------------------------------------------
def make_wood(name="Wood"):
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

# ---------------------------------------------------------------------------
# Material registries
# ---------------------------------------------------------------------------
CUP_REGISTRY = [
    # decorative_metal
    (make_brushed_metal, 1.0),
    (make_galvanized_metal, 1.0),
    (make_grained_metal, 1.0),
    (make_hammered_metal, 0.7),
    # decorative_hard extras
    (make_vase_ceramic, 4.0),
    (make_colored_glass, 2.0),
    (make_marble, 1.0),
    (make_glass_volume, 2.0),
    (make_ceramic, 1.0),
    # cup extras
    (make_metal_basic, 2.0),
    (make_plastic, 5.0),
    (make_plastic_translucent, 5.0),
    (make_glass, 3.0),
]

WOODS_REGISTRY = [
    (make_wood, 1.0),
]

# ---------------------------------------------------------------------------
# Scene helpers
# ---------------------------------------------------------------------------
def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    bpy.context.scene.cursor.location = (0, 0, 0)

def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
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

def read_co(obj):
    arr = np.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", arr)
    return arr.reshape(-1, 3)

def subsurf(obj, levels, simple=False):
    if levels > 0:
        modify_mesh(obj, "SUBSURF",
                    levels=levels, render_levels=levels,
                    subdivision_type="SIMPLE" if simple else "CATMULL_CLARK")

def origin2lowest(obj, vertical=False):
    co = read_co(obj)
    if not len(co):
        return
    i = np.argmin(co[:, -1])
    if vertical:
        obj.location[2] = -co[i, 2]
    else:
        obj.location = -co[i]
    apply_transform(obj, loc=True)

def new_base_circle(vertices=32):
    bpy.ops.mesh.primitive_circle_add(location=(0, 0, 0), vertices=vertices)
    return bpy.context.active_object

def new_base_cylinder(vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    apply_transform(obj, loc=True)
    return obj

def join_objects(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.location = 0, 0, 0
    obj.rotation_euler = 0, 0, 0
    obj.scale = 1, 1, 1
    bpy.ops.object.select_all(action="DESELECT")
    return obj

def delete_obj(obj):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------------------------------------------------------------------------
# PanFactory geometry (verbatim from objects_blender/tableware/PanFactory.py)
# ---------------------------------------------------------------------------
def add_handle(obj, x_handle, z_handle, z_handle_mid, s_handle):
    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_mode(type="EDGE")
    bm = bmesh.from_edit_mesh(obj.data)
    bm.edges.ensure_lookup_table()
    m = []
    for e in bm.edges:
        u, v = e.verts
        m.append(u.co[0] + v.co[0] + u.co[2] + v.co[2])
    ri = np.argmax(m)
    for e in bm.edges:
        e.select_set(bool(e.index == ri))
    bm.select_flush(False)
    bmesh.update_edit_mesh(obj.data)

    bpy.ops.mesh.extrude_edges_move(
        TRANSFORM_OT_translate={"value": (x_handle * 0.5, 0, z_handle_mid)}
    )
    bpy.ops.mesh.extrude_edges_move(
        TRANSFORM_OT_translate={"value": (x_handle * 0.5, 0, z_handle - z_handle_mid)}
    )
    bpy.ops.transform.resize(value=[s_handle] * 3)
    bpy.ops.mesh.extrude_edges_move(
        TRANSFORM_OT_translate={"value": (1e-3, 0, 0)}
    )
    bpy.ops.object.mode_set(mode="OBJECT")

def add_handle_hole(obj, r_expand, x_handle):
    cutter = new_base_cylinder()
    cutter.scale = *([uniform(0.06, 0.1)] * 2), 1
    cutter.location[0] = r_expand + uniform(0.8, 0.9) * x_handle
    select_only(obj)
    mod = obj.modifiers.new("Boolean", "BOOLEAN")
    mod.object = cutter
    mod.operation = "DIFFERENCE"
    mod.solver = "FLOAT"
    bpy.ops.object.modifier_apply(modifier=mod.name)
    delete_obj(cutter)

def add_guard(obj, x_guard, guard_depth):
    """Extrude faces where x > x_guard outward by guard_depth, mark as guard (mat_index=1).

    This replicates the TablewareFactory.add_guard GeoNodes approach:
    ExtrudeMesh on selection(x > x_guard) + StoreNamedAttribute("guard").
    Here we do it with bmesh since no NodeWrangler is available.
    """

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    bm.normal_update()

    # Select faces where face center x > x_guard
    guard_faces = []
    for face in bm.faces:
        center = face.calc_center_median()
        if center.x > x_guard:
            guard_faces.append(face)

    if not guard_faces:
        bm.free()
        return

    # Extrude and translate along individual face normals
    result = bmesh.ops.extrude_discrete_faces(bm, faces=guard_faces)
    extruded_faces = result["faces"]

    for face in extruded_faces:
        offset = face.normal * guard_depth
        for vert in face.verts:
            vert.co += offset

    # Mark extruded faces + their side faces with material_index=1
    # The side faces are created automatically between original and extruded faces.
    # They have verts shared with extruded faces but are not in extruded_faces list.
    # Simple heuristic: after extrusion, all NEW faces (those not in original) that
    # share verts with extruded faces are side faces.
    extruded_set = set(extruded_faces)
    extruded_verts = set()
    for f in extruded_faces:
        for v in f.verts:
            extruded_verts.add(v)

    bm.faces.ensure_lookup_table()
    for face in bm.faces:
        if face in extruded_set:
            face.material_index = 1
        else:
            # Side faces share verts with extruded faces
            face_verts = set(face.verts)
            if face_verts & extruded_verts and face.material_index == 0:
                # Check if ALL verts are in extruded_verts (side face)
                # Side faces from discrete extrude share some verts with extruded
                # Actually for discrete extrude, side faces connect old+new verts.
                # We mark faces that have at least one extruded vert AND have a
                # normal that is roughly perpendicular to the surface (side face).
                pass  # We'll use a simpler approach below

    # Simpler approach: mark all faces with center x > x_guard as guard
    # (including the extruded top faces and any side faces in that region)
    for face in bm.faces:
        if face in extruded_set:
            face.material_index = 1
            continue
        center = face.calc_center_median()
        if center.x > x_guard:
            face.material_index = 1

    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()

def make_base(n, depth, r_expand, r_mid, has_handle, x_handle, z_handle,
              z_handle_mid, s_handle, has_handle_hole, thickness,
              has_guard, x_guard, guard_depth):
    base = new_base_circle(vertices=n)
    middle = new_base_circle(vertices=n)
    middle.location[2] = depth / 2
    middle.scale = [r_mid] * 3
    upper = new_base_circle(vertices=n)
    upper.location[2] = depth
    upper.scale = [r_expand] * 3
    apply_transform(upper, loc=True)
    obj = join_objects([base, middle, upper])

    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.bridge_edge_loops()
    bm = bmesh.from_edit_mesh(obj.data)
    for v in bm.verts:
        v.select_set(bool(np.abs(v.co[2]) < 1e-3))
    bm.select_flush(False)
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode="OBJECT")

    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.fill_grid(use_interp_simple=True, offset=np.random.randint(n // 4))
    bpy.ops.mesh.quads_convert_to_tris(quad_method="BEAUTY", ngon_method="BEAUTY")
    bpy.ops.object.mode_set(mode="OBJECT")

    obj.rotation_euler[2] = np.pi / n
    apply_transform(obj)

    if has_handle:
        add_handle(obj, x_handle, z_handle, z_handle_mid, s_handle)

    # Solidify (matches solidify_with_inside but without inside attribute
    # since PanFactory has_inside=False)
    modify_mesh(obj, "SOLIDIFY", thickness=thickness, offset=1)

    # Guard extrusion (before subsurf, matching order)
    if has_guard:
        add_guard(obj, x_guard, guard_depth)

    subsurf(obj, 1, True)
    subsurf(obj, 3)

    if has_handle_hole:
        add_handle_hole(obj, r_expand, x_handle)

    return obj

# ---------------------------------------------------------------------------
# Main creation function
# ---------------------------------------------------------------------------
def create_pan(seed):
    """Create a pan mesh with materials assigned."""
    # --- Geometry params (factory_seed RNG) ---
    seed_all(seed)

    r_expand = 1 if uniform(0, 1) < 0.2 else float(log_uniform(1.0, 1.2))
    depth = float(log_uniform(0.3, 0.8))
    if r_expand == 1:
        r_mid = float(log_uniform(1.0, 1.3))
    else:
        r_mid = 1 + (r_expand - 1) * (uniform(0.5, 0.85) if uniform(0, 1) < 0.5 else 0.5)
    has_handle = True
    has_handle_hole = uniform() < 0.6
    x_handle = float(log_uniform(1.2, 2.0))
    z_handle = x_handle * uniform(0, 0.2)
    z_handle_mid = uniform(0.6, 0.8) * z_handle
    s_handle = float(log_uniform(0.8, 1.2))
    thickness = float(log_uniform(0.04, 0.06))
    has_guard = uniform(0, 1) < 0.8
    x_guard = r_expand + uniform(0, 0.2) * x_handle
    guard_depth = float(log_uniform(1.0, 2.0) * thickness)
    scale = float(log_uniform(0.1, 0.15))

    # --- Materials (sampled under separate seed for independence) ---
    mat_seed = int_hash((seed, 0))
    seed_all(mat_seed)

    # Main surface from cup pool
    make_fn = weighted_sample(CUP_REGISTRY)
    surface_mat = make_fn(name="PanSurface")

    # Guard surface from woods pool (only used if has_guard)
    guard_mat = make_wood(name="GuardSurface") if has_guard else None

    # --- Build geometry (restore geometry seed) ---
    seed_all(seed)
    # Re-consume __init__ draws to align RNG state for create_asset
    _ = uniform(0, 1)  # r_expand check
    if _ >= 0.2:
        _ = log_uniform(1.0, 1.2)
    _ = log_uniform(0.3, 0.8)  # depth
    # r_mid draws
    if r_expand == 1:
        _ = log_uniform(1.0, 1.3)
    else:
        _ = uniform(0, 1)  # branch check
        if _ < 0.5:
            _ = uniform(0.5, 0.85)
    _ = uniform()  # has_handle_hole
    _ = log_uniform(1.2, 2.0)  # x_handle
    _ = uniform(0, 0.2)  # z_handle factor
    _ = uniform(0.6, 0.8)  # z_handle_mid factor
    _ = log_uniform(0.8, 1.2)  # s_handle
    _ = log_uniform(0.04, 0.06)  # thickness
    _ = uniform(0, 1)  # has_guard
    _ = uniform(0, 0.2)  # x_guard factor
    _ = log_uniform(1.0, 2.0)  # guard_depth factor
    _ = log_uniform(0.1, 0.15)  # scale

    # Now RNG is at create_asset position
    n = 4 * int(log_uniform(4, 8))
    obj = make_base(n, depth, r_expand, r_mid, has_handle, x_handle, z_handle,
                    z_handle_mid, s_handle, has_handle_hole, thickness,
                    has_guard, x_guard, guard_depth)
    origin2lowest(obj, vertical=True)
    obj.scale = [scale] * 3
    apply_transform(obj)

    # Shade smooth
    select_only(obj)
    bpy.ops.object.shade_smooth()

    # --- Assign materials ---
    # Slot 0: main surface
    obj.data.materials.append(surface_mat)

    # Slot 1: guard surface (wood) -- only if has_guard
    if has_guard and guard_mat is not None:
        obj.data.materials.append(guard_mat)
        # material_index=1 was already set by add_guard()

    obj.name = "PanFactory"
    return obj

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
clear_scene()
pan = create_pan(SEED)
print(f"PanFactory: seed={SEED}, verts={len(pan.data.vertices)}, "
      f"materials={len(pan.data.materials)}")

