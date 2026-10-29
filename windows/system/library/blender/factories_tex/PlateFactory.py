# [FL_INDEX: keywords="blender_factory, procedural_3d, PlateFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: PlateFactory | Category: factories_tex
# Prompt: A 3D model of a round dinner plate rendered from a slightly elevated three-quarter perspective. The plate features a flat circular form with a wide shallow well in the center, a raised rim border around the edge, a dark navy-blue coloring with subtle surface variation, and a small ring base on the underside.

"""PlateFactory — standalone textured plate (ceramic/glass/metal/plastic + wear_tear).

Shader pool mirrors material_assignments.cup (used by TablewareFactory):
  decorative_metal: BrushedMetal(1), GalvanizedMetal(1), GrainedMetal(1), HammeredMetal(1)
  + VaseCeramic(4), ColoredGlass(2), Marble(1), GlassVolume(2), Ceramic(1)
  + MetalBasic(2), Plastic(5), PlasticTranslucent(5), Glass(3)

Guard (wood) pool mirrors material_assignments.woods — sampled during Phase 1
to preserve raw-seed RNG consumption order even though
PlateFactory sets has_guard=False and never applies the guard material.

Wear-tear: 50% chance scratches, 50% chance edge_wear — applied on top of the
body (and inside) material exactly as in TablewareFactory.finalize_assets.

Per-part material assignment (mirrors TablewareFactory.finalize_assets + PlateFactory):
  * body surface        = cup registry sample 1
  * inside surface      = cup registry sample 2 (only if has_inside, ~20% chance)
  * guard surface       = woods sample          (never applied: has_guard=False)
  * scratches/edge wear = wear_tear helpers     (each independently 50/50)

Geometry: copied verbatim from objects_blender/tableware/PlateFactory.py
(spin revolution body with anchors [0, x_mid, x_mid, x_end] + pre-SUBSURF +
SOLIDIFY + SUBSURF).
"""


import os
import hashlib
import math
import random
import colorsys
from collections.abc import Sized

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
def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

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

def _math(nt, op, a, b):
    node = nt.nodes.new("ShaderNodeMath")
    node.operation = op
    if hasattr(a, "outputs"):
        nt.links.new(a.outputs[0] if hasattr(a.outputs[0], "links") else a, node.inputs[0])
    elif isinstance(a, (int, float)):
        node.inputs[0].default_value = float(a)
    else:
        nt.links.new(a, node.inputs[0])

    if hasattr(b, "outputs"):
        nt.links.new(b.outputs[0] if hasattr(b.outputs[0], "links") else b, node.inputs[1])
    elif isinstance(b, (int, float)):
        node.inputs[1].default_value = float(b)
    else:
        nt.links.new(b, node.inputs[1])
    return node

def _connect_output(nt, bsdf, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    return out

# ---------------------------------------------------------------------------
# Material factories — inlined translations of shaders
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

# --- VaseCeramic -----------------------------------------------------------
def make_vase_ceramic(name="VaseCeramic"):
    mat = _new_material(name)
    nt = mat.node_tree
    hsv = (uniform(0.0, 1.0), uniform(0.0, 0.75), uniform(0.0, 0.3))
    color = hsv2rgba(hsv)

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
    hsv = (uniform(0.0, 1.0), uniform(0.0, 0.2), 1.0)
    glass = nt.nodes.new("ShaderNodeBsdfPrincipled")
    glass.inputs["Base Color"].default_value = hsv2rgba(hsv)
    glass.inputs["Roughness"].default_value = float(uniform(0.05, 0.2))
    _connect_output(nt, glass)
    return mat

# --- Marble ----------------------------------------------------------------
def make_marble(name="Marble"):
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # Scale + rotate
    scale_node = nt.nodes.new("ShaderNodeVectorMath")
    scale_node.operation = "SCALE"
    nt.links.new(tex_coord.outputs["Object"], scale_node.inputs[0])

    rotate_node = nt.nodes.new("ShaderNodeVectorRotate")
    rotate_node.rotation_type = "EULER_XYZ"
    nt.links.new(scale_node.outputs["Vector"], rotate_node.inputs["Vector"])

    seed_val = 0.0
    scale_val = 3.0
    add_val = scale_val + 1.0

    # Noise 1
    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    noise1.noise_dimensions = "4D"
    nt.links.new(rotate_node.outputs["Vector"], noise1.inputs["Vector"])
    noise1.inputs["W"].default_value = seed_val
    noise1.inputs["Scale"].default_value = scale_val
    noise1.inputs["Detail"].default_value = 15.0

    # Noise 2 (scale + 1)
    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    noise2.noise_dimensions = "4D"
    nt.links.new(rotate_node.outputs["Vector"], noise2.inputs["Vector"])
    noise2.inputs["W"].default_value = seed_val
    noise2.inputs["Scale"].default_value = add_val
    noise2.inputs["Detail"].default_value = 15.0

    # Map range on noise2 fac
    mr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(_noise_fac_output(noise2), mr.inputs["Value"])
    mr.inputs[1].default_value = 0.48
    mr.inputs[2].default_value = 0.60

    # Noise 3 based on noise1 fac
    noise3 = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(_noise_fac_output(noise1), noise3.inputs["Vector"])
    noise3.inputs["Scale"].default_value = 8.0
    noise3.inputs["Detail"].default_value = 15.0

    # Voronoi on noise3
    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.feature = "DISTANCE_TO_EDGE"
    voronoi.voronoi_dimensions = "4D"
    nt.links.new(_noise_fac_output(noise3), voronoi.inputs["Vector"])
    voronoi.inputs["W"].default_value = 1.64
    voronoi.inputs["Scale"].default_value = 3.0

    cr1 = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(voronoi.outputs["Distance"], cr1.inputs["Fac"])
    cr1.color_ramp.elements[0].position = 0.0
    cr1.color_ramp.elements[0].color = (1, 1, 1, 1)
    cr1.color_ramp.elements[1].position = 0.03
    cr1.color_ramp.elements[1].color = (0, 0, 0, 1)

    mul_mr_cr1 = _math(nt, "MULTIPLY", mr.outputs["Result"], cr1.outputs["Color"])

    # Mix noise1 + noise4
    noise4 = nt.nodes.new("ShaderNodeTexNoise")
    noise4.noise_dimensions = "4D"
    nt.links.new(_noise_fac_output(noise1), noise4.inputs["Vector"])
    noise4.inputs["W"].default_value = seed_val
    noise4.inputs["Scale"].default_value = 8.0
    noise4.inputs["Detail"].default_value = 15.0

    mix1 = nt.nodes.new("ShaderNodeMix")
    mix1.data_type = "RGBA"
    mix1.inputs[0].default_value = 0.8
    nt.links.new(_noise_fac_output(noise1), mix1.inputs[6])
    nt.links.new(_noise_fac_output(noise4), mix1.inputs[7])

    cr2 = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(mix1.outputs[2], cr2.inputs["Fac"])
    cr2.color_ramp.elements[0].position = 0.3
    cr2.color_ramp.elements[0].color = (1, 1, 1, 1)
    cr2.color_ramp.elements[1].position = 0.9
    cr2.color_ramp.elements[1].color = (0, 0, 0, 1)

    mix2 = nt.nodes.new("ShaderNodeMix")
    mix2.data_type = "RGBA"
    nt.links.new(mul_mr_cr1.outputs[0], mix2.inputs[0])
    nt.links.new(cr2.outputs["Color"], mix2.inputs[6])
    mix2.inputs[7].default_value = (0.0376, 0.0179, 0.0033, 1.0)

    # Displacement
    disp = nt.nodes.new("ShaderNodeDisplacement")
    nt.links.new(mul_mr_cr1.outputs[0], disp.inputs["Height"])
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.02

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix1.outputs[2], bsdf.inputs["Base Color"])
    _set_principled(bsdf, **{"Specular IOR Level": 0.6, "Roughness": 0.1})
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# --- GlassVolume -----------------------------------------------------------
def make_glass_volume(name="GlassVolume"):
    mat = _new_material(name)
    nt = mat.node_tree
    if np.random.uniform() < 0.3:
        color = (1, 1, 1, 1)
    else:
        color = hsv2rgba((uniform(0, 1), uniform(0.5, 0.9), uniform(0.6, 0.9)))

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=0.0, **{"Transmission Weight": 1.0})

    vol = nt.nodes.new("ShaderNodeVolumeAbsorption")
    vol.inputs["Color"].default_value = color
    vol.inputs["Density"].default_value = 100.0

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    nt.links.new(vol.outputs[0], out.inputs["Volume"])
    return mat

# --- Glass -----------------------------------------------------------------
def make_glass(name="Glass"):
    mat = _new_material(name)
    nt = mat.node_tree
    glass = nt.nodes.new("ShaderNodeBsdfPrincipled")
    glass.inputs["Roughness"].default_value = 0.02
    glass.inputs["IOR"].default_value = 1.5
    if "Transmission Weight" in glass.inputs:
        glass.inputs["Transmission Weight"].default_value = 1.0
    elif "Transmission" in glass.inputs:
        glass.inputs["Transmission"].default_value = 1.0
    _connect_output(nt, glass)
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
    _set_principled(bsdf, Metallic=1.0,
                    **{"Specular IOR Level": float(np.random.uniform(0.5, 1.0)),
                       "Base Color": hsv2rgba(color_hsv or metal_hsv())})
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

# --- BrushedMetal ----------------------------------------------------------
def make_brushed_metal(name="BrushedMetal"):
    mat = _new_material(name)
    nt = mat.node_tree
    base_color = hsv2rgba(metal_hsv())
    scale = 1.0
    seed_val = float(uniform(-1000, 1000))

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # Stretched mapping for brush streaks
    mapping1 = nt.nodes.new("ShaderNodeMapping")
    mapping1.inputs["Scale"].default_value = (0.2, 0.2, 5.0)
    nt.links.new(tex_coord.outputs["Object"], mapping1.inputs["Vector"])

    mul_scale = _math(nt, "MULTIPLY", scale, 100.0)

    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    noise1.noise_dimensions = "4D"
    nt.links.new(mapping1.outputs["Vector"], noise1.inputs["Vector"])
    noise1.inputs["W"].default_value = seed_val
    nt.links.new(mul_scale.outputs[0], noise1.inputs["Scale"])
    noise1.inputs["Detail"].default_value = 15.0
    noise1.inputs["Roughness"].default_value = 0.4
    noise1.inputs["Distortion"].default_value = 0.1

    # Second noise with distorted coords
    mapping2 = nt.nodes.new("ShaderNodeMapping")
    mapping2.inputs["Scale"].default_value = (1.0, 1.0, 20.0)
    nt.links.new(tex_coord.outputs["Object"], mapping2.inputs["Vector"])

    noise_low = nt.nodes.new("ShaderNodeTexNoise")
    noise_low.noise_dimensions = "4D"
    nt.links.new(tex_coord.outputs["Object"], noise_low.inputs["Vector"])
    noise_low.inputs["W"].default_value = seed_val
    noise_low.inputs["Scale"].default_value = 0.1
    noise_low.inputs["Detail"].default_value = 15.0
    noise_low.inputs["Roughness"].default_value = 0.0

    mix_vec = nt.nodes.new("ShaderNodeMix")
    mix_vec.data_type = "RGBA"
    mix_vec.inputs[0].default_value = 0.2
    nt.links.new(mapping2.outputs["Vector"], mix_vec.inputs[6])
    nt.links.new(noise_low.outputs["Color"], mix_vec.inputs[7])

    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    noise2.noise_dimensions = "4D"
    nt.links.new(mix_vec.outputs[2], noise2.inputs["Vector"])
    noise2.inputs["W"].default_value = seed_val
    nt.links.new(mul_scale.outputs[0], noise2.inputs["Scale"])
    noise2.inputs["Detail"].default_value = 15.0
    noise2.inputs["Roughness"].default_value = 0.6
    noise2.inputs["Distortion"].default_value = 0.1

    # Darken blend
    mix_dark = nt.nodes.new("ShaderNodeMix")
    mix_dark.data_type = "RGBA"
    mix_dark.blend_type = "DARKEN"
    mix_dark.inputs[0].default_value = 1.0
    nt.links.new(_noise_fac_output(noise1), mix_dark.inputs[6])
    nt.links.new(_noise_fac_output(noise2), mix_dark.inputs[7])

    # Color variation
    mr_color = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(mix_dark.outputs[2], mr_color.inputs["Value"])
    mr_color.inputs[1].default_value = 0.4
    mr_color.inputs[2].default_value = 0.6
    mr_color.inputs[3].default_value = 0.8
    mr_color.inputs[4].default_value = 1.2

    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    nt.links.new(mr_color.outputs["Result"], hsv_node.inputs["Value"])
    hsv_node.inputs["Color"].default_value = base_color

    # Roughness variation
    mr_rough = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(mix_dark.outputs[2], mr_rough.inputs["Value"])
    mr_rough.inputs[1].default_value = 0.4
    mr_rough.inputs[2].default_value = 0.6
    mr_rough.inputs[3].default_value = 0.2
    mr_rough.inputs[4].default_value = 0.3

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(hsv_node.outputs["Color"], bsdf.inputs["Base Color"])
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})
    nt.links.new(mr_rough.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

# --- GalvanizedMetal -------------------------------------------------------
def make_galvanized_metal(name="GalvanizedMetal"):
    mat = _new_material(name)
    nt = mat.node_tree
    base_color = hsv2rgba(metal_hsv())
    scale = 1.0
    seed_val = float(uniform(-1000, 1000))

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mul_s = _math(nt, "MULTIPLY", scale, 5.0)

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["W"].default_value = seed_val
    nt.links.new(mul_s.outputs[0], noise.inputs["Scale"])
    noise.inputs["Detail"].default_value = 15.0
    noise.inputs["Roughness"].default_value = 0.4
    noise.inputs["Distortion"].default_value = 0.2

    mix_vec = nt.nodes.new("ShaderNodeMix")
    mix_vec.data_type = "RGBA"
    mix_vec.clamp_factor = False
    mix_vec.inputs[0].default_value = 0.05
    nt.links.new(tex_coord.outputs["Object"], mix_vec.inputs[6])
    nt.links.new(noise.outputs["Color"], mix_vec.inputs[7])

    mul_v = _math(nt, "MULTIPLY", scale, 500.0)

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.voronoi_dimensions = "4D"
    voronoi.distance = "MINKOWSKI"
    nt.links.new(mix_vec.outputs[2], voronoi.inputs["Vector"])
    voronoi.inputs["W"].default_value = seed_val
    nt.links.new(mul_v.outputs[0], voronoi.inputs["Scale"])

    mr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(voronoi.outputs["Color"], mr.inputs["Value"])
    mr.inputs[3].default_value = 0.1
    mr.inputs[4].default_value = 0.5

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = base_color
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

# --- GrainedMetal ----------------------------------------------------------
def make_grained_metal(name="GrainedMetal"):
    mat = _new_material(name)
    nt = mat.node_tree
    base_color = hsv2rgba(metal_hsv())
    scale = 1.0
    seed_val = float(uniform(-1000, 1000))
    roughness = float(uniform(0.0, 1.0))

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mr_rough = nt.nodes.new("ShaderNodeMapRange")
    mr_rough.inputs["Value"].default_value = roughness
    mr_rough.inputs[3].default_value = 0.05
    mr_rough.inputs[4].default_value = 0.25

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = base_color
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})
    nt.links.new(mr_rough.outputs["Result"], bsdf.inputs["Roughness"])

    mul_scale = _math(nt, "MULTIPLY", scale, 2000.0)

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["W"].default_value = seed_val
    nt.links.new(mul_scale.outputs[0], noise.inputs["Scale"])
    noise.inputs["Detail"].default_value = 15.0
    noise.inputs["Distortion"].default_value = 2.0

    mul1 = _math(nt, "MULTIPLY", mr_rough.outputs["Result"], 0.4)
    mul2 = _math(nt, "MULTIPLY", _noise_fac_output(noise), mul1.outputs[0])
    mul3 = _math(nt, "MULTIPLY", mul2.outputs[0], 0.01)

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul3.outputs[0], disp.inputs["Height"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# --- HammeredMetal ---------------------------------------------------------
def make_hammered_metal(name="HammeredMetal"):
    mat = _new_material(name)
    nt = mat.node_tree
    base_color = hsv2rgba(metal_hsv())
    scale = log_uniform(0.8, 1.2)
    seed_val = float(uniform(-1000, 1000))

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = base_color
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0, "Roughness": 0.1})

    mul_s = _math(nt, "MULTIPLY", scale, 20.0)

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["W"].default_value = seed_val
    nt.links.new(mul_s.outputs[0], noise.inputs["Scale"])
    noise.inputs["Detail"].default_value = 15.0
    noise.inputs["Roughness"].default_value = 0.4
    noise.inputs["Distortion"].default_value = 0.2

    mix_vec = nt.nodes.new("ShaderNodeMix")
    mix_vec.data_type = "RGBA"
    mix_vec.clamp_factor = False
    mix_vec.inputs[0].default_value = 0.01
    nt.links.new(tex_coord.outputs["Object"], mix_vec.inputs[6])
    nt.links.new(noise.outputs["Color"], mix_vec.inputs[7])

    mul_v = _math(nt, "MULTIPLY", scale, 300.0)

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.voronoi_dimensions = "4D"
    voronoi.feature = "SMOOTH_F1"
    try:
        voronoi.inputs["Smoothness"].default_value = 0.2
    except Exception:
        pass
    nt.links.new(mix_vec.outputs[2], voronoi.inputs["Vector"])
    voronoi.inputs["W"].default_value = seed_val
    nt.links.new(mul_v.outputs[0], voronoi.inputs["Scale"])

    mul_dist = _math(nt, "MULTIPLY", voronoi.outputs["Distance"], scale)
    power = _math(nt, "POWER", mul_dist.outputs[0], 2.5)
    mul_disp = _math(nt, "MULTIPLY", power.outputs[0], log_uniform(0.001, 0.003))

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_disp.outputs[0], disp.inputs["Height"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# --- BrushedBlackMetal -----------------------------------------------------
def make_brushed_black_metal(name="BrushedBlackMetal"):
    mat = _new_material(name)
    nt = mat.node_tree
    # ShaderNodeBsdfAnisotropic may be unavailable; fall back to glossy
    try:
        node = nt.nodes.new("ShaderNodeBsdfAnisotropic")
    except Exception:
        node = nt.nodes.new("ShaderNodeBsdfGlossy")
    node.inputs["Color"].default_value = (0.0167, 0.0167, 0.0167, 1.0)
    _connect_output(nt, node)
    return mat

# --- Plastic (rough) ------------------------------------------------------
def make_plastic_rough(name="Plastic"):
    mat = _new_material(name)
    nt = mat.node_tree
    roughness = float(uniform(0.0, 1.0))
    seed_val = float(uniform(-1000, 1000))
    base_color = hsv2rgba((uniform(0, 1), uniform(0.5, 0.8), log_uniform(0.01, 0.5)))

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["Value"].default_value = roughness
    mr.inputs[3].default_value = 0.05
    mr.inputs[4].default_value = 0.25

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = base_color
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])

    mul_scale = _math(nt, "MULTIPLY", 1.0, 2000.0)

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["W"].default_value = seed_val
    nt.links.new(mul_scale.outputs[0], noise.inputs["Scale"])
    noise.inputs["Detail"].default_value = 15.0
    noise.inputs["Distortion"].default_value = 2.0

    mul1 = _math(nt, "MULTIPLY", mr.outputs["Result"], 0.4)
    mul2 = _math(nt, "MULTIPLY", _noise_fac_output(noise), mul1.outputs[0])
    mul3 = _math(nt, "MULTIPLY", mul2.outputs[0], 0.003)

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul3.outputs[0], disp.inputs["Height"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# --- PlasticTranslucent ---------------------------------------------------
def make_plastic_translucent(name="PlasticTranslucent"):
    mat = _new_material(name)
    nt = mat.node_tree
    base_color = hsv2rgba((uniform(0, 1), uniform(0.5, 0.8), log_uniform(0.4, 0.8)))

    layer_w = nt.nodes.new("ShaderNodeLayerWeight")
    layer_w.inputs["Blend"].default_value = float(uniform(0.2, 0.4))

    glass = nt.nodes.new("ShaderNodeBsdfPrincipled")
    glass.inputs["Base Color"].default_value = base_color
    glass.inputs["Roughness"].default_value = 0.2
    glass.inputs["IOR"].default_value = float(uniform(1.2, 1.6))
    if "Transmission Weight" in glass.inputs:
        glass.inputs["Transmission Weight"].default_value = 1.0
    elif "Transmission" in glass.inputs:
        glass.inputs["Transmission"].default_value = 1.0

    glossy = nt.nodes.new("ShaderNodeBsdfGlossy")
    glossy.inputs["Roughness"].default_value = 0.2

    mix_sh = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(layer_w.outputs["Fresnel"], mix_sh.inputs["Fac"])
    nt.links.new(glass.outputs[0], mix_sh.inputs[1])
    nt.links.new(glossy.outputs[0], mix_sh.inputs[2])

    _connect_output(nt, mix_sh)
    return mat

# ---------------------------------------------------------------------------
# Material registry mirroring material_assignments.cup
# ---------------------------------------------------------------------------
CUP_REGISTRY = [
    # decorative_metal
    (make_brushed_metal, 1.0),
    (make_galvanized_metal, 1.0),
    (make_grained_metal, 1.0),
    (make_hammered_metal, 1.0),
    # decorative_hard extras
    (make_vase_ceramic, 4.0),
    (make_colored_glass, 2.0),
    (make_marble, 1.0),
    (make_glass_volume, 2.0),
    (make_ceramic, 1.0),
    # cup extras
    (make_metal_basic, 2.0),
    (make_plastic_rough, 5.0),
    (make_plastic_translucent, 5.0),
    (make_glass, 3.0),
]

# ---------------------------------------------------------------------------
# Wear-tear: scratches (displacement only) + edge_wear (shader + displacement)
# ---------------------------------------------------------------------------
def apply_scratches(obj):
    """Translation of wear_tear/scratches.py — adds displacement scratches."""

    params = {
        "angle1": float(uniform(10, 80)),
        "angle2": float(uniform(-80, -10)),
        "scratch_scale": log_uniform(5, 80),
        "scratch_mask_ratio": log_uniform(0.01, 0.9),
        "scratch_mask_noise": log_uniform(5, 40),
        "scratch_depth": log_uniform(0.1, 1.0),
    }
    for mat in obj.data.materials:
        if mat is None or not mat.use_nodes:
            continue
        nt = mat.node_tree
        if any(n.label == "scratch" for n in nt.nodes):
            continue

        # Find output node
        out_nodes = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"]
        if not out_nodes:
            continue
        out_node = out_nodes[0]

        tex_coord = nt.nodes.new("ShaderNodeTexCoord")

        # Direction 1
        cxyz1 = nt.nodes.new("ShaderNodeCombineXYZ")
        cxyz1.inputs["Y"].default_value = params["angle1"]
        m1 = nt.nodes.new("ShaderNodeMapping")
        m1.vector_type = "TEXTURE"
        m1.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
        nt.links.new(tex_coord.outputs["Object"], m1.inputs["Vector"])
        nt.links.new(cxyz1.outputs[0], m1.inputs["Rotation"])

        n1 = nt.nodes.new("ShaderNodeTexNoise")
        nt.links.new(m1.outputs["Vector"], n1.inputs["Vector"])
        n1.inputs["Scale"].default_value = params["scratch_scale"]
        n1.inputs["Detail"].default_value = 15.0
        n1.inputs["Roughness"].default_value = 0.0
        n1.inputs["Distortion"].default_value = 22.8

        # Direction 2
        cxyz2 = nt.nodes.new("ShaderNodeCombineXYZ")
        cxyz2.inputs["Y"].default_value = params["angle2"]
        m2 = nt.nodes.new("ShaderNodeMapping")
        m2.vector_type = "TEXTURE"
        m2.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
        nt.links.new(tex_coord.outputs["Object"], m2.inputs["Vector"])
        nt.links.new(cxyz2.outputs[0], m2.inputs["Rotation"])

        n2 = nt.nodes.new("ShaderNodeTexNoise")
        nt.links.new(m2.outputs["Vector"], n2.inputs["Vector"])
        n2.inputs["Scale"].default_value = params["scratch_scale"]
        n2.inputs["Detail"].default_value = 15.0
        n2.inputs["Roughness"].default_value = 0.0
        n2.inputs["Distortion"].default_value = 22.8

        add_n = _math(nt, "ADD", _noise_fac_output(n1), _noise_fac_output(n2))

        # Mask noise
        m3 = nt.nodes.new("ShaderNodeMapping")
        m3.vector_type = "TEXTURE"
        m3.inputs["Rotation"].default_value = (0.1588, -0.5742, 0.192)
        nt.links.new(tex_coord.outputs["Object"], m3.inputs["Vector"])

        n3 = nt.nodes.new("ShaderNodeTexNoise")
        nt.links.new(m3.outputs["Vector"], n3.inputs["Vector"])
        n3.inputs["Scale"].default_value = params["scratch_mask_noise"]
        n3.inputs["Detail"].default_value = 1.0

        cr = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(_noise_fac_output(n3), cr.inputs["Fac"])
        cr.color_ramp.elements[0].position = 0.4109
        cr.color_ramp.elements[0].color = (0, 0, 0, 1)
        cr.color_ramp.elements[1].position = 1.0
        cr.color_ramp.elements[1].color = (1, 1, 1, 1)

        mul_mask = _math(nt, "MULTIPLY", params["scratch_mask_ratio"], cr.outputs["Color"])

        add_clamped = nt.nodes.new("ShaderNodeMath")
        add_clamped.operation = "ADD"
        add_clamped.use_clamp = True
        nt.links.new(add_n.outputs[0], add_clamped.inputs[0])
        nt.links.new(mul_mask.outputs[0], add_clamped.inputs[1])

        mr = nt.nodes.new("ShaderNodeMapRange")
        nt.links.new(add_clamped.outputs[0], mr.inputs["Value"])
        mr.inputs[1].default_value = 0.7
        mr.inputs[2].default_value = 0.72
        mr.inputs[4].default_value = 0.9

        disp = nt.nodes.new("ShaderNodeDisplacement")
        nt.links.new(mr.outputs["Result"], disp.inputs["Height"])
        disp.inputs["Midlevel"].default_value = 0.0
        disp.inputs["Scale"].default_value = params["scratch_depth"]

        nt.links.new(disp.outputs[0], out_node.inputs["Displacement"])
        disp.label = "scratch"

def apply_edge_wear(obj):
    """Translation of wear_tear/edge_wear.py — mixes in worn-edge shader."""

    params = {
        "_worn_off_opacity": float(uniform(0.01)),
        "_worn_off_radius": float(uniform(0.005, 0.01)),
        "_scratch_radius": float(uniform(0.01, 0.03)),
        "_worn_off_mask_randomness": float(uniform(2.5, 3.0)),
        "_edge_base_color_hue": float(uniform(0.0, 1.0)),
        "_edge_base_color_whiteness": float(uniform(0.1, 0.6)),
        "_scratch_mask_randomness": float(np.random.choice(
            [uniform(0.1, 5.0), uniform(1.0, 10.0)])),
        "_scratch_density": float(np.random.choice([uniform(1.5, 10.0)])),
        "_scratch_opacity": float(uniform(0.5, 1.0)),
    }

    for mat in obj.data.materials:
        if mat is None or not mat.use_nodes:
            continue
        nt = mat.node_tree

        if any(n.label == "wear_tear" for n in nt.nodes):
            continue

        out_nodes = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"]
        if not out_nodes:
            continue
        out_node = out_nodes[0]

        surf_links = out_node.inputs["Surface"].links
        if not surf_links:
            continue
        original_bsdf = surf_links[0].from_node

        disp_links = out_node.inputs["Displacement"].links
        original_displacement = disp_links[0].from_node if disp_links else None

        # --- Build edge wear shader graph ---
        tex_coord = nt.nodes.new("ShaderNodeTexCoord")
        mapping = nt.nodes.new("ShaderNodeMapping")
        nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

        # Scratch mask noise
        noise_sm = nt.nodes.new("ShaderNodeTexNoise")
        nt.links.new(mapping.outputs["Vector"], noise_sm.inputs["Vector"])
        noise_sm.inputs["Scale"].default_value = params["_scratch_mask_randomness"]
        noise_sm.inputs["Detail"].default_value = 1.0

        cr_sm = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(_noise_fac_output(noise_sm), cr_sm.inputs["Fac"])
        cr_sm.color_ramp.elements[0].position = 0.4436
        cr_sm.color_ramp.elements[0].color = (0, 0, 0, 1)
        cr_sm.color_ramp.elements[1].position = 0.5345
        cr_sm.color_ramp.elements[1].color = (1, 1, 1, 1)

        # Bevel for scratch edges
        bevel1 = nt.nodes.new("ShaderNodeBevel")
        bevel1.samples = 20
        bevel1.inputs["Radius"].default_value = params["_scratch_radius"]

        geom = nt.nodes.new("ShaderNodeNewGeometry")

        sub1 = nt.nodes.new("ShaderNodeVectorMath")
        sub1.operation = "SUBTRACT"
        nt.links.new(bevel1.outputs[0], sub1.inputs[0])
        nt.links.new(geom.outputs["Normal"], sub1.inputs[1])

        abs1 = nt.nodes.new("ShaderNodeMath")
        abs1.operation = "ABSOLUTE"
        nt.links.new(sub1.outputs["Vector"], abs1.inputs[0])

        cr1 = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(abs1.outputs[0], cr1.inputs["Fac"])
        cr1.color_ramp.elements[0].position = 0.0691
        cr1.color_ramp.elements[0].color = (0, 0, 0, 1)
        cr1.color_ramp.elements[1].position = 0.1564
        cr1.color_ramp.elements[1].color = (1, 1, 1, 1)

        mul_sm_cr1 = nt.nodes.new("ShaderNodeMath")
        mul_sm_cr1.operation = "MULTIPLY"
        mul_sm_cr1.use_clamp = True
        nt.links.new(cr_sm.outputs["Color"], mul_sm_cr1.inputs[0])
        nt.links.new(cr1.outputs["Color"], mul_sm_cr1.inputs[1])

        mul_scratch_opacity = nt.nodes.new("ShaderNodeMath")
        mul_scratch_opacity.operation = "MULTIPLY"
        mul_scratch_opacity.use_clamp = True
        mul_scratch_opacity.inputs[0].default_value = params["_scratch_opacity"]
        nt.links.new(mul_sm_cr1.outputs[0], mul_scratch_opacity.inputs[1])

        # Paint worn-off (bevel2)
        bevel2 = nt.nodes.new("ShaderNodeBevel")
        bevel2.samples = 20
        bevel2.inputs["Radius"].default_value = params["_worn_off_radius"]

        sub2 = nt.nodes.new("ShaderNodeVectorMath")
        sub2.operation = "SUBTRACT"
        nt.links.new(bevel2.outputs[0], sub2.inputs[0])
        nt.links.new(geom.outputs["Normal"], sub2.inputs[1])

        abs2 = nt.nodes.new("ShaderNodeMath")
        abs2.operation = "ABSOLUTE"
        nt.links.new(sub2.outputs["Vector"], abs2.inputs[0])

        noise_wo = nt.nodes.new("ShaderNodeTexNoise")
        nt.links.new(mapping.outputs["Vector"], noise_wo.inputs["Vector"])
        noise_wo.inputs["Scale"].default_value = params["_worn_off_mask_randomness"]
        noise_wo.inputs["Detail"].default_value = 1.0

        cr_wo = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(_noise_fac_output(noise_wo), cr_wo.inputs["Fac"])
        cr_wo.color_ramp.elements[0].position = 0.0764
        cr_wo.color_ramp.elements[0].color = (1, 1, 1, 1)
        cr_wo.color_ramp.elements[1].position = 0.5709
        cr_wo.color_ramp.elements[1].color = (0, 0, 0, 1)

        mul_wo = nt.nodes.new("ShaderNodeMath")
        mul_wo.operation = "MULTIPLY"
        mul_wo.use_clamp = True
        nt.links.new(abs2.outputs[0], mul_wo.inputs[0])
        nt.links.new(cr_wo.outputs["Color"], mul_wo.inputs[1])

        mul_wo_opacity = nt.nodes.new("ShaderNodeMath")
        mul_wo_opacity.operation = "MULTIPLY"
        mul_wo_opacity.use_clamp = True
        mul_wo_opacity.inputs[0].default_value = params["_worn_off_opacity"]
        nt.links.new(mul_wo.outputs[0], mul_wo_opacity.inputs[1])

        cr3 = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(mul_wo_opacity.outputs[0], cr3.inputs["Fac"])
        cr3.color_ramp.elements[0].position = 0.0
        cr3.color_ramp.elements[0].color = (0, 0, 0, 1)
        cr3.color_ramp.elements[1].position = 0.7782
        cr3.color_ramp.elements[1].color = (1, 1, 1, 1)

        # Edge color
        combine_color = nt.nodes.new("ShaderNodeCombineColor")
        combine_color.mode = "HSV"
        combine_color.inputs["Red"].default_value = params["_edge_base_color_hue"]
        combine_color.inputs["Green"].default_value = 0.7733
        combine_color.inputs["Blue"].default_value = 0.01

        mix_edge_color = nt.nodes.new("ShaderNodeMix")
        mix_edge_color.data_type = "RGBA"
        mix_edge_color.clamp_result = True
        mix_edge_color.inputs[0].default_value = params["_edge_base_color_whiteness"]
        nt.links.new(combine_color.outputs[0], mix_edge_color.inputs[6])
        mix_edge_color.inputs[7].default_value = (0.02, 0.02, 0.02, 1.0)

        edge_bsdf1 = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(mix_edge_color.outputs[2], edge_bsdf1.inputs["Base Color"])
        _set_principled(edge_bsdf1, Metallic=0.3745, **{"Specular IOR Level": 0.0, "Roughness": 0.1436})

        mix_sh1 = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(cr3.outputs["Color"], mix_sh1.inputs["Fac"])
        nt.links.new(original_bsdf.outputs[0], mix_sh1.inputs[1])
        nt.links.new(edge_bsdf1.outputs[0], mix_sh1.inputs[2])

        # Scratch voronoi pattern
        mapping_v1 = nt.nodes.new("ShaderNodeMapping")
        mapping_v1.inputs["Scale"].default_value = (10.0, 1.0, 1.0)
        nt.links.new(tex_coord.outputs["Object"], mapping_v1.inputs["Vector"])

        vor1 = nt.nodes.new("ShaderNodeTexVoronoi")
        vor1.feature = "DISTANCE_TO_EDGE"
        nt.links.new(mapping_v1.outputs["Vector"], vor1.inputs["Vector"])
        vor1.inputs["Scale"].default_value = params["_scratch_density"]

        mapping_v2 = nt.nodes.new("ShaderNodeMapping")
        mapping_v2.inputs["Scale"].default_value = (1.0, 10.0, 1.0)
        nt.links.new(tex_coord.outputs["Object"], mapping_v2.inputs["Vector"])

        vor2 = nt.nodes.new("ShaderNodeTexVoronoi")
        vor2.feature = "DISTANCE_TO_EDGE"
        nt.links.new(mapping_v2.outputs["Vector"], vor2.inputs["Vector"])
        vor2.inputs["Scale"].default_value = params["_scratch_density"] * 2.0

        mul_vor = nt.nodes.new("ShaderNodeMath")
        mul_vor.operation = "MULTIPLY"
        mul_vor.use_clamp = True
        nt.links.new(vor1.outputs["Distance"], mul_vor.inputs[0])
        nt.links.new(vor2.outputs["Distance"], mul_vor.inputs[1])

        cr6 = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(mul_vor.outputs[0], cr6.inputs["Fac"])
        cr6.color_ramp.elements[0].position = 0.0
        cr6.color_ramp.elements[0].color = (1, 1, 1, 1)
        cr6.color_ramp.elements[1].position = 0.0073
        cr6.color_ramp.elements[1].color = (0, 0, 0, 1)

        mul_edge_scratch = nt.nodes.new("ShaderNodeMath")
        mul_edge_scratch.operation = "MULTIPLY"
        mul_edge_scratch.use_clamp = True
        nt.links.new(cr1.outputs["Color"], mul_edge_scratch.inputs[0])
        nt.links.new(cr6.outputs["Color"], mul_edge_scratch.inputs[1])

        mul_combined = nt.nodes.new("ShaderNodeMath")
        mul_combined.operation = "MULTIPLY"
        mul_combined.use_clamp = True
        nt.links.new(mul_sm_cr1.outputs[0], mul_combined.inputs[0])
        nt.links.new(mul_edge_scratch.outputs[0], mul_combined.inputs[1])

        edge_bsdf2 = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(mix_edge_color.outputs[2], edge_bsdf2.inputs["Base Color"])
        _set_principled(edge_bsdf2, Metallic=0.3855, **{"Specular IOR Level": 0.0, "Roughness": 0.0})

        mix_sh2 = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(mul_scratch_opacity.outputs[0], mix_sh2.inputs["Fac"])
        nt.links.new(mix_sh1.outputs[0], mix_sh2.inputs[1])
        nt.links.new(edge_bsdf2.outputs[0], mix_sh2.inputs[2])

        nt.links.new(mix_sh2.outputs[0], out_node.inputs["Surface"])

        # Displacement from scratches
        scale_mul6 = nt.nodes.new("ShaderNodeVectorMath")
        scale_mul6.operation = "SCALE"
        nt.links.new(mul_combined.outputs[0], scale_mul6.inputs[0])
        scale_mul6.inputs["Scale"].default_value = 2.0

        if original_displacement is not None:
            add_disp = nt.nodes.new("ShaderNodeMath")
            add_disp.operation = "ADD"
            add_disp.use_clamp = True
            nt.links.new(original_displacement.outputs[0], add_disp.inputs[0])
            nt.links.new(scale_mul6.outputs["Vector"], add_disp.inputs[1])
            nt.links.new(add_disp.outputs[0], out_node.inputs["Displacement"])
        else:
            nt.links.new(scale_mul6.outputs["Vector"], out_node.inputs["Displacement"])

        mix_sh2.label = "wear_tear"

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

# ---------------------------------------------------------------------------
# Spin (revolution body) — from objects_blender/tableware/BowlFactory.py
# ---------------------------------------------------------------------------
def bezier_curve(anchors, vector_locations=(), resolution=None):
    n = [len(r) for r in anchors if isinstance(r, Sized)][0]
    anchors = np.array([
        np.array(r, dtype=float) if isinstance(r, Sized) else np.full(n, r)
        for r in anchors
    ])
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    if n > 2:
        select_only(obj)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.curve.subdivide(number_cuts=n - 2)
        bpy.ops.object.mode_set(mode="OBJECT")
    points = obj.data.splines[0].bezier_points
    for i in range(n):
        points[i].co = anchors[:, i]
    for i in range(n):
        if i in vector_locations:
            points[i].handle_left_type = "VECTOR"
            points[i].handle_right_type = "VECTOR"
        else:
            points[i].handle_left_type = "AUTO"
            points[i].handle_right_type = "AUTO"
    obj.data.splines[0].resolution_u = resolution if resolution is not None else 12
    return curve2mesh(obj)

def curve2mesh(obj):
    points = obj.data.splines[0].bezier_points
    cos = np.array([p.co for p in points])
    length = np.linalg.norm(cos[:-1] - cos[1:], axis=-1)
    min_length = 5e-3
    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    for i in range(len(points)):
        if points[i].handle_left_type == "FREE":
            points[i].handle_left_type = "ALIGNED"
        if points[i].handle_right_type == "FREE":
            points[i].handle_right_type = "ALIGNED"
    for i in reversed(range(len(points) - 1)):
        points = list(obj.data.splines[0].bezier_points)
        number_cuts = min(int(length[i] / min_length) - 1, 64)
        if number_cuts < 0:
            continue
        bpy.ops.curve.select_all(action="DESELECT")
        points[i].select_control_point = True
        points[i + 1].select_control_point = True
        bpy.ops.curve.subdivide(number_cuts=number_cuts)
    obj.data.splines[0].resolution_u = 1
    bpy.ops.object.mode_set(mode="OBJECT")
    select_only(obj)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.active_object
    modify_mesh(obj, "WELD", merge_threshold=1e-3)
    return obj

def spin(anchors, vector_locations=(), rotation_resolution=None, axis=(0, 0, 1)):
    obj = bezier_curve(anchors, vector_locations)
    co = read_co(obj)
    ax = np.array(axis)
    mean_radius = np.mean(np.linalg.norm(
        co - (co @ ax)[:, np.newaxis] * ax, axis=-1
    ))
    if rotation_resolution is None:
        rotation_resolution = min(int(2 * np.pi * mean_radius / 5e-3), 128)
    modify_mesh(obj, "WELD", merge_threshold=1e-3)
    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.spin(steps=rotation_resolution, angle=np.pi * 2, axis=axis)
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=1e-3)
    bpy.ops.object.mode_set(mode="OBJECT")
    return obj

# ---------------------------------------------------------------------------
# Plate geometry + material application
# ---------------------------------------------------------------------------
# Geometry body is copied verbatim from objects_blender/tableware/PlateFactory.py.
#   cup(surface), cup(inside), wear_tear(scratch/edge) — under the raw factory
def create_plate(seed):
    """Create a plate mesh, assign cup-pool materials, optionally apply wear-tear."""
    # --- Geometry RNG (mirrors objects_blender/tableware/PlateFactory.py) ---
    seed_all(seed)

    x_end = 0.5
    z_length = float(log_uniform(0.05, 0.2))
    x_mid = float(uniform(0.3, 1.0)) * x_end
    z_mid = float(uniform(0.3, 0.8)) * z_length
    pre_level = 1
    scale = float(log_uniform(0.2, 0.4))
    thickness = float(uniform(0.01, 0.03)) * scale

    x_anchors = (0, x_mid, x_mid, x_end)
    z_anchors = (0, 0, z_mid, z_length)
    anchors = np.array(x_anchors) * scale, 0, np.array(z_anchors) * scale
    obj = spin(anchors, [1, 2])
    modify_mesh(obj, "SUBSURF", render_levels=pre_level, levels=pre_level)
    modify_mesh(obj, "SOLIDIFY", thickness=thickness, offset=1)
    subsurf(obj, 1)

    # Shade smooth
    select_only(obj)
    bpy.ops.object.shade_smooth()

    # --- Material RNG: mirror factory_seed draws in TablewareFactory
    #     __init__ + PlateFactory.__init__. Use int_hash((seed, 0)) for the
    #     create_asset-level seed, matching BowlFactory's convention.
    asset_seed = int_hash((seed, 0))
    seed_all(asset_seed)

    # Sample surface from cup pool
    make_surface = weighted_sample(CUP_REGISTRY)
    surface_mat = make_surface(name="PlateSurface")

    # Sample inside from cup pool (consumed even if unused, to match draw order)
    make_inside = weighted_sample(CUP_REGISTRY)
    inside_mat = make_inside(name="PlateInside")

    # lower_thresh controls the band of inside faces that get the inside material
    lower_thresh = float(uniform(0.5, 0.8))

    # PlateFactory.__init__ draws: z_length, x_mid, z_mid, has_inside, scale, thickness
    _ = float(log_uniform(0.05, 0.2))          # z_length (material-RNG mirror)
    _ = float(uniform(0.3, 1.0)) * 0.5         # x_mid
    _ = float(uniform(0.3, 0.8))               # z_mid
    has_inside = float(uniform(0, 1)) < 0.2
    _ = float(log_uniform(0.2, 0.4))           # scale
    _ = float(uniform(0.01, 0.03))             # thickness

    # Body material goes to slot 0 (all faces by default)
    obj.data.materials.append(surface_mat)

    if has_inside:
        # Slot 1: inside material on the concave/inner band below lower_thresh
        obj.data.materials.append(inside_mat)
        co = read_co(obj)
        max_z = float(np.max(co[:, -1])) if len(co) else 0.0
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        for face in bm.faces:
            center = face.calc_center_median()
            radial = math.sqrt(center.x * center.x + center.y * center.y)
            if radial < 1e-6:
                continue
            radial_dot = face.normal.x * center.x + face.normal.y * center.y
            if radial_dot < 0 and center.z < max_z * lower_thresh:
                face.material_index = 1
        bm.to_mesh(obj.data)
        bm.free()

    # Wear-tear: 50% chance each, applied to all materials on the object
    scratch_prob = 0.5
    edge_wear_prob = 0.5
    if float(np.random.uniform()) <= scratch_prob:
        apply_scratches(obj)
    if float(np.random.uniform()) <= edge_wear_prob:
        apply_edge_wear(obj)

    obj.name = "Plate"
    return obj

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
clear_scene()
plate = create_plate(SEED)
print(f"PlateFactory: seed={SEED}, verts={len(plate.data.vertices)}, "
      f"material_slots={len(plate.data.materials)}")

