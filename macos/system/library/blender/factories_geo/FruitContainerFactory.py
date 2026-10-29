# [FL_INDEX: keywords="blender_factory, procedural_3d, FruitContainerFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: FruitContainerFactory | Category: factories_geo
# Prompt: A 3D model of a wide shallow fruit bowl filled with round fruits rendered from a slightly elevated three-quarter perspective. The bowl features a wide rim, a low cylindrical profile, a dark matte exterior, and is filled with multiple round smooth spherical fruits arranged loosely inside.

"""FruitContainerFactory -- textured fruit container (bowl/pot + scattered fruits).

Seeding: FixedSeed(SEED) for material params, FixedSeed(int_hash((SEED,0))) for geometry.
Wear-tear: 50% scratch / 50% edge_wear gates sampled under initial SEED block.
"""


import os
import hashlib
import math
import random
import colorsys
from collections.abc import Sized

import bmesh
import bpy
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


# hex -> hex2rgba (srgb_to_linear) -> rgb2hsv
_NATURAL_BASE_HSV = [
    (0.0,    0.0,    0.5271),  # 0xC0C0C0 silver
    (0.0961, 0.6702, 0.2623),  # 0x8C7853 khaki
    (0.1319, 0.1682, 0.5089),  # 0xBDBAAE light gray
    (0.6296, 0.1518, 0.4678),  # 0xA9ACB6 gray-blue
    (0.0749, 0.1518, 0.4678),  # 0xB6AFA9 gray-beige
]


def metal_natural_hsv():
    """See implementation."""

    idx = np.random.randint(0, len(_NATURAL_BASE_HSV))
    h, s, v = _NATURAL_BASE_HSV[idx]
    return (
        h + float(np.random.uniform(-0.1, 0.1)),
        s + float(np.random.uniform(-0.1, 0.1)),
        v * float(log_uniform(0.2, 0.5)),
    )


def metal_hsv():
    """See implementation."""

    if np.random.uniform() < 0.2:
        return metal_natural_hsv()
    return (np.random.uniform(0, 1),
            np.random.uniform(0.3, 0.6),
            log_uniform(0.02, 0.5))

def weighted_sample(registry):
    classes, weights = zip(*registry)
    weights = np.array(weights, dtype=float)
    return classes[int(np.random.choice(len(classes), p=weights / weights.sum()))]


class FixedSeed:
    def __init__(self, seed):
        self.seed = int(seed)
    def __enter__(self):
        self._py = random.getstate()
        self._np = np.random.get_state()
        random.seed(self.seed)
        np.random.seed(self.seed)
    def __exit__(self, *_):
        random.setstate(self._py)
        np.random.set_state(self._np)


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
# Container material factories -- inlined from BowlFactory (cup registry)
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
    glass = nt.nodes.new("ShaderNodeBsdfGlass")
    glass.inputs["Color"].default_value = hsv2rgba(hsv)
    glass.inputs["Roughness"].default_value = float(uniform(0.05, 0.2))
    _connect_output(nt, glass)
    return mat


# --- Marble ----------------------------------------------------------------
def make_marble(name="Marble"):
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    scale_node = nt.nodes.new("ShaderNodeVectorMath")
    scale_node.operation = "SCALE"
    nt.links.new(tex_coord.outputs["Object"], scale_node.inputs[0])

    rotate_node = nt.nodes.new("ShaderNodeVectorRotate")
    rotate_node.rotation_type = "EULER_XYZ"
    nt.links.new(scale_node.outputs["Vector"], rotate_node.inputs["Vector"])

    seed_val = 0.0
    scale_val = 3.0
    add_val = scale_val + 1.0

    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    noise1.noise_dimensions = "4D"
    nt.links.new(rotate_node.outputs["Vector"], noise1.inputs["Vector"])
    noise1.inputs["W"].default_value = seed_val
    noise1.inputs["Scale"].default_value = scale_val
    noise1.inputs["Detail"].default_value = 15.0

    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    noise2.noise_dimensions = "4D"
    nt.links.new(rotate_node.outputs["Vector"], noise2.inputs["Vector"])
    noise2.inputs["W"].default_value = seed_val
    noise2.inputs["Scale"].default_value = add_val
    noise2.inputs["Detail"].default_value = 15.0

    mr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(_noise_fac_output(noise2), mr.inputs["Value"])
    mr.inputs[1].default_value = 0.48
    mr.inputs[2].default_value = 0.60

    noise3 = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(_noise_fac_output(noise1), noise3.inputs["Vector"])
    noise3.inputs["Scale"].default_value = 8.0
    noise3.inputs["Detail"].default_value = 15.0

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
    glass = nt.nodes.new("ShaderNodeBsdfGlass")
    glass.inputs["Roughness"].default_value = 0.02
    glass.inputs["IOR"].default_value = 1.5
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

    mix_dark = nt.nodes.new("ShaderNodeMix")
    mix_dark.data_type = "RGBA"
    mix_dark.blend_type = "DARKEN"
    mix_dark.inputs[0].default_value = 1.0
    nt.links.new(_noise_fac_output(noise1), mix_dark.inputs[6])
    nt.links.new(_noise_fac_output(noise2), mix_dark.inputs[7])

    mr_color = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(mix_dark.outputs[2], mr_color.inputs["Value"])
    mr_color.inputs[1].default_value = 0.4
    mr_color.inputs[2].default_value = 0.6
    mr_color.inputs[3].default_value = 0.8
    mr_color.inputs[4].default_value = 1.2

    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    nt.links.new(mr_color.outputs["Result"], hsv_node.inputs["Value"])
    hsv_node.inputs["Color"].default_value = base_color

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

    glass = nt.nodes.new("ShaderNodeBsdfGlass")
    glass.inputs["Color"].default_value = base_color
    glass.inputs["Roughness"].default_value = 0.2
    glass.inputs["IOR"].default_value = float(uniform(1.2, 1.6))

    glossy = nt.nodes.new("ShaderNodeBsdfGlossy")
    glossy.inputs["Roughness"].default_value = 0.2

    mix_sh = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(layer_w.outputs["Fresnel"], mix_sh.inputs["Fac"])
    nt.links.new(glass.outputs[0], mix_sh.inputs[1])
    nt.links.new(glossy.outputs[0], mix_sh.inputs[2])

    _connect_output(nt, mix_sh)
    return mat


def make_plastic(name="Plastic"):
    """See implementation."""

    is_rough = float(np.random.uniform(0, 1))
    is_translucent = float(np.random.uniform(0, 1))
    if is_rough > is_translucent:
        return make_plastic_rough(name)
    else:
        return make_plastic_translucent(name)


# ---------------------------------------------------------------------------
# Container material registry -- mirrors material_assignments.cup
# ---------------------------------------------------------------------------
CUP_REGISTRY = [
    (make_brushed_metal, 1.0),
    (make_galvanized_metal, 1.0),
    (make_grained_metal, 1.0),
    (make_hammered_metal, 1.0),
    (make_vase_ceramic, 4.0),
    (make_colored_glass, 2.0),
    (make_marble, 1.0),
    (make_glass_volume, 2.0),
    (make_ceramic, 1.0),
    (make_metal_basic, 2.0),
    (make_plastic, 5.0),
    (make_plastic_translucent, 5.0),
    (make_glass, 3.0),
]


# ---------------------------------------------------------------------------
# Wear-tear: scratches + edge_wear (from BowlFactory)
# ---------------------------------------------------------------------------
def apply_scratches(obj):
    """See implementation."""

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

        out_nodes = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"]
        if not out_nodes:
            continue
        out_node = out_nodes[0]

        tex_coord = nt.nodes.new("ShaderNodeTexCoord")

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
    """See implementation."""

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

        tex_coord = nt.nodes.new("ShaderNodeTexCoord")
        mapping = nt.nodes.new("ShaderNodeMapping")
        nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

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
        _set_principled(edge_bsdf1, Metallic=0.3745,
                        **{"Specular IOR Level": 0.0, "Roughness": 0.1436})

        mix_sh1 = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(cr3.outputs["Color"], mix_sh1.inputs["Fac"])
        nt.links.new(original_bsdf.outputs[0], mix_sh1.inputs[1])
        nt.links.new(edge_bsdf1.outputs[0], mix_sh1.inputs[2])

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
        _set_principled(edge_bsdf2, Metallic=0.3855,
                        **{"Specular IOR Level": 0.0, "Roughness": 0.0})

        mix_sh2 = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(mul_scratch_opacity.outputs[0], mix_sh2.inputs["Fac"])
        nt.links.new(mix_sh1.outputs[0], mix_sh2.inputs[1])
        nt.links.new(edge_bsdf2.outputs[0], mix_sh2.inputs[2])

        nt.links.new(mix_sh2.outputs[0], out_node.inputs["Surface"])

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
# Fruit material factories -- subsurface-scattering Principled BSDF
# ---------------------------------------------------------------------------
def _make_fruit_material(fruit_type):
    """Create a subsurface-scattering material for a given fruit type."""

    mat = _new_material(f"Fruit_{fruit_type}")
    nt = mat.node_tree

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    if fruit_type == "apple":
        base_hsv = (uniform(-0.05, 0.1), uniform(0.8, 0.999), uniform(0.6, 0.9))
        alt_hsv = (uniform(0.25, 0.4), uniform(0.6, 0.95), uniform(0.3, 0.7))
        sss_weight = 0.15
    elif fruit_type == "orange":
        base_hsv = (uniform(0.06, 0.12), uniform(0.85, 0.999), uniform(0.7, 0.95))
        alt_hsv = (uniform(0.08, 0.14), uniform(0.7, 0.9), uniform(0.5, 0.8))
        sss_weight = 0.2
    elif fruit_type == "lemon":
        base_hsv = (uniform(0.13, 0.18), uniform(0.85, 0.999), uniform(0.8, 0.98))
        alt_hsv = (uniform(0.15, 0.22), uniform(0.7, 0.95), uniform(0.6, 0.9))
        sss_weight = 0.15
    elif fruit_type == "pear":
        base_hsv = (uniform(0.18, 0.35), uniform(0.5, 0.85), uniform(0.4, 0.75))
        alt_hsv = (uniform(0.05, 0.15), uniform(0.6, 0.9), uniform(0.3, 0.6))
        sss_weight = 0.12
    else:  # plum
        base_hsv = (uniform(0.7, 0.85), uniform(0.4, 0.8), uniform(0.15, 0.4))
        alt_hsv = (uniform(0.75, 0.9), uniform(0.3, 0.6), uniform(0.1, 0.3))
        sss_weight = 0.1

    base_color = hsv2rgba(base_hsv)
    alt_color = hsv2rgba(alt_hsv)

    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    noise1.noise_dimensions = "4D"
    nt.links.new(tex_coord.outputs["Object"], noise1.inputs["Vector"])
    noise1.inputs["W"].default_value = float(uniform(-100, 100))
    noise1.inputs["Scale"].default_value = float(uniform(3, 8))
    noise1.inputs["Detail"].default_value = 5.0
    noise1.inputs["Roughness"].default_value = 0.5

    # Map range for blend factor
    mr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(_noise_fac_output(noise1), mr.inputs["Value"])
    mr.inputs[1].default_value = 0.3
    mr.inputs[2].default_value = 0.7

    # Mix base and alt colors
    mix_color = nt.nodes.new("ShaderNodeMix")
    mix_color.data_type = "RGBA"
    nt.links.new(mr.outputs["Result"], mix_color.inputs[0])
    mix_color.inputs[6].default_value = base_color
    mix_color.inputs[7].default_value = alt_color

    # Fine surface bumps (orange peel, apple skin texture)
    noise_bump = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(tex_coord.outputs["Object"], noise_bump.inputs["Vector"])
    noise_bump.inputs["Scale"].default_value = float(uniform(30, 80))
    noise_bump.inputs["Detail"].default_value = 8.0
    noise_bump.inputs["Roughness"].default_value = 0.6

    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = float(uniform(0.05, 0.15))
    bump.inputs["Distance"].default_value = 0.002
    nt.links.new(_noise_fac_output(noise_bump), bump.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix_color.outputs[2], bsdf.inputs["Base Color"])
    _set_principled(bsdf, **{
        "Roughness": float(uniform(0.3, 0.6)),
        "Subsurface Weight": sss_weight,
        "Specular IOR Level": float(uniform(0.3, 0.5)),
    })
    # Subsurface color (slightly warmer/lighter version of base)
    if "Subsurface Radius" in bsdf.inputs:
        bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.5, 0.25)
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    _connect_output(nt, bsdf)
    return mat


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


def write_co(obj, arr):
    obj.data.vertices.foreach_set("co", arr.reshape(-1))
    obj.data.update()


def subsurf(obj, levels, simple=False):
    if levels > 0:
        modify_mesh(obj, "SUBSURF",
                     levels=levels, render_levels=levels,
                     subdivision_type="SIMPLE" if simple else "CATMULL_CLARK")


def new_base_circle(vertices=32):
    bpy.ops.mesh.primitive_circle_add(location=(0, 0, 0), vertices=vertices)
    return bpy.context.active_object


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


# ---------------------------------------------------------------------------
# Spin (revolution body) -- from objects_blender/tableware/FruitContainerFactory.py
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
# Pot creation (circle + bridge) -- verbatim from objects_blender version
# ---------------------------------------------------------------------------
def create_pot(depth, r_expand, r_mid, thickness, pot_scale):
    n = 4 * int(log_uniform(4, 8))
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

    modify_mesh(obj, "SOLIDIFY", thickness=thickness, offset=1)
    subsurf(obj, 1, True)
    subsurf(obj, 3)

    obj.scale = [pot_scale] * 3
    apply_transform(obj)
    return obj


# ---------------------------------------------------------------------------
# Bowl creation (spin revolution) -- verbatim from objects_blender version
# ---------------------------------------------------------------------------
def create_bowl():
    x_end = 0.5
    z_length = float(log_uniform(0.4, 0.8))
    z_bottom = float(log_uniform(0.02, 0.05))
    x_bottom = uniform(0.2, 0.3) * x_end
    x_mid = uniform(0.8, 0.95) * x_end
    scale = float(log_uniform(0.15, 0.4))
    thickness = uniform(0.01, 0.03) * scale

    x_anchors = (0, x_bottom, x_bottom + 1e-3, x_bottom, x_mid, x_end)
    z_anchors = (0, 0, 0, z_bottom, z_length / 2, z_length)
    anchors = np.array(x_anchors) * scale, 0, np.array(z_anchors) * scale

    obj = spin(anchors, [2, 3])
    modify_mesh(obj, "SOLIDIFY", thickness=thickness, offset=1)
    modify_mesh(obj, "BEVEL", width=thickness / 2, segments=np.random.randint(2, 5))
    subsurf(obj, 1)
    return obj


# ---------------------------------------------------------------------------
# Procedural fruit -- verbatim from objects_blender version
# ---------------------------------------------------------------------------
def create_fruit_template(fruit_seed, fruit_type):
    """Create a single procedural fruit (deformed sphere)."""

    np.random.seed(fruit_seed)
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=16, ring_count=8, radius=1.0, location=(0, 0, 0))
    obj = bpy.context.active_object

    co = read_co(obj)

    if fruit_type == "apple":
        co[:, 0] *= uniform(0.9, 1.05)
        co[:, 1] *= uniform(0.9, 1.05)
        co[:, 2] *= uniform(0.85, 0.95)
        top_mask = co[:, 2] > 0.7
        co[top_mask, 2] -= 0.1 * (co[top_mask, 2] - 0.7) ** 0.5
        bot_mask = co[:, 2] < -0.7
        co[bot_mask, 2] += 0.08 * (-co[bot_mask, 2] - 0.7) ** 0.5

    elif fruit_type == "orange":
        co[:, 0] *= uniform(0.95, 1.05)
        co[:, 1] *= uniform(0.95, 1.05)
        co[:, 2] *= uniform(0.92, 1.02)
        bump = 1.0 + 0.03 * np.sin(co[:, 0:1] * 20) * np.cos(co[:, 1:2] * 18) * np.sin(co[:, 2:] * 16)
        co *= bump

    elif fruit_type == "lemon":
        co[:, 0] *= uniform(0.7, 0.85)
        co[:, 1] *= uniform(0.7, 0.85)
        co[:, 2] *= uniform(1.2, 1.5)
        z_abs = np.abs(co[:, 2])
        tip_mask = z_abs > 0.8
        tip_factor = np.clip((z_abs[tip_mask] - 0.8) / 0.5, 0, 1)
        co[tip_mask, 0] *= (1.0 - 0.5 * tip_factor)
        co[tip_mask, 1] *= (1.0 - 0.5 * tip_factor)

    elif fruit_type == "pear":
        z_norm = (co[:, 2] + 1.0) / 2.0
        width_factor = 1.0 - 0.35 * z_norm ** 1.5
        co[:, 0] *= width_factor * uniform(0.95, 1.05)
        co[:, 1] *= width_factor * uniform(0.95, 1.05)
        co[:, 2] *= uniform(1.1, 1.3)

    else:  # plum
        co[:, 0] *= uniform(0.9, 1.0)
        co[:, 1] *= uniform(0.9, 1.0)
        co[:, 2] *= uniform(0.85, 0.95)
        bump = 1.0 + 0.02 * np.sin(co[:, 0:1] * 12) * np.cos(co[:, 1:2] * 10)
        co *= bump

    write_co(obj, co)
    subsurf(obj, 1)

    # Assign fruit material
    fruit_mat = _make_fruit_material(fruit_type)
    obj.data.materials.append(fruit_mat)

    return obj


# ---------------------------------------------------------------------------
# Inner surface detection -- verbatim from objects_blender version
# ---------------------------------------------------------------------------
def get_inner_lower_faces(container, lower_thresh=0.65):
    mesh = container.data
    mesh.update()

    centers = []
    normals = []
    areas = []
    for poly in mesh.polygons:
        centers.append(np.array(poly.center))
        normals.append(np.array(poly.normal))
        areas.append(float(poly.area))
    centers = np.array(centers)
    normals = np.array(normals)
    areas = np.array(areas)

    if len(centers) == 0:
        return np.array([]), np.array([]), np.array([]), np.array([])

    max_z = centers[:, 2].max()
    z_thresh = max_z * lower_thresh

    r = np.sqrt(centers[:, 0] ** 2 + centers[:, 1] ** 2)

    n_bins = 20
    z_min, z_max = centers[:, 2].min(), centers[:, 2].max()
    z_range = max(z_max - z_min, 1e-6)
    bin_idx = np.clip(((centers[:, 2] - z_min) / z_range * n_bins).astype(int), 0, n_bins - 1)
    max_r_per_bin = np.zeros(n_bins)
    for b in range(n_bins):
        mask = bin_idx == b
        if mask.any():
            max_r_per_bin[b] = r[mask].max()

    max_r_at_face = max_r_per_bin[bin_idx]
    is_inner = r < max_r_at_face * 0.85
    is_lower = centers[:, 2] < z_thresh

    r_safe = np.maximum(r, 1e-8)
    radial_dir = np.column_stack([centers[:, 0] / r_safe, centers[:, 1] / r_safe])
    radial_normal = normals[:, 0] * radial_dir[:, 0] + normals[:, 1] * radial_dir[:, 1]
    is_inward = (radial_normal < 0) | (normals[:, 2] > 0.5)

    selection = is_inner & is_lower & is_inward
    sel_idx = np.nonzero(selection)[0]

    return sel_idx, centers, normals, areas


def random_point_on_face(mesh, poly_idx):
    poly = mesh.polygons[poly_idx]
    verts = [mesh.vertices[vi].co for vi in poly.vertices]
    if len(verts) < 3:
        return np.array(poly.center)
    v0 = np.array(verts[0])
    v1 = np.array(verts[1])
    v2 = np.array(verts[2])
    r1, r2 = np.random.random(), np.random.random()
    if r1 + r2 > 1:
        r1, r2 = 1 - r1, 1 - r2
    return v0 + r1 * (v1 - v0) + r2 * (v2 - v0)


# ---------------------------------------------------------------------------
# Fruit scatter -- verbatim from objects_blender version
# ---------------------------------------------------------------------------
def scatter_fruits(container, n_fruits, fruit_scale, scale_rand, fruit_seed):
    np.random.seed(fruit_seed)
    mesh = container.data
    mesh.update()

    sel_idx, centers, normals, areas = get_inner_lower_faces(container, lower_thresh=0.80)

    if len(sel_idx) == 0:
        return []

    sel_centers = centers[sel_idx]
    sel_normals = normals[sel_idx]
    sel_areas = areas[sel_idx]
    total_area = sel_areas.sum()

    n_target = min(n_fruits, max(1, int(1e3 * total_area)))
    face_probs = sel_areas / total_area

    fruit_types = ["apple", "orange", "lemon", "pear", "plum"]
    templates = []
    for i in range(5):
        t = create_fruit_template(fruit_seed + 100 + i, fruit_types[i])
        templates.append(t)

    placed = []
    copies = []
    chosen = np.random.choice(len(sel_idx), size=n_target * 5, p=face_probs)

    ground_offset_factor = 0.6

    for fi in chosen:
        if len(copies) >= n_target:
            break

        poly_idx = sel_idx[fi]
        pos = random_point_on_face(mesh, poly_idx)
        nrm = sel_normals[fi]

        pos = pos + nrm * fruit_scale * ground_offset_factor
        if pos[2] < fruit_scale * 0.5:
            pos[2] = fruit_scale * 0.5

        if placed:
            dists = np.linalg.norm(np.array(placed) - pos, axis=1)
            if np.any(dists < fruit_scale * 1.6):
                continue

        placed.append(pos.copy())

        src = templates[np.random.randint(len(templates))]
        copy = src.copy()
        copy.data = src.data.copy()
        bpy.context.scene.collection.objects.link(copy)

        s = fruit_scale * (1.0 - scale_rand * np.random.uniform())
        copy.scale = [s] * 3
        copy.location = pos.tolist()
        copy.rotation_euler = (
            uniform(-0.3, 0.3),
            uniform(-0.3, 0.3),
            uniform(0, 2 * np.pi)
        )
        apply_transform(copy, loc=True)
        copies.append(copy)

    for t in templates:
        bpy.data.objects.remove(t, do_unlink=True)

    return copies


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------
def build(seed):
    clear_scene()

    # Geometry params inside FixedSeed; do NOT seed_all() beforehand because
    # the geo-only version has no np.random.seed() before its FixedSeed block.
    # After FixedSeed exits, the restored numpy state must match the geo-only
    # version's (uninitialized) state so that create_bowl/create_pot draw the
    # same random values.
    with FixedSeed(seed):
        use_bowl = uniform() < 0.5
        scale_rand = uniform(0.1, 0.3)
        n_fruits = np.random.randint(8, 25)
        fruit_seed = np.random.randint(1e6)

        pot_depth = float(log_uniform(0.6, 2.0))
        pot_r_expand = 1.0
        pot_r_mid = 1.0
        pot_thickness = float(log_uniform(0.04, 0.06))
        pot_scale = float(log_uniform(0.1, 0.15))

    if use_bowl:
        container = create_bowl()
    else:
        container = create_pot(pot_depth, pot_r_expand, pot_r_mid,
                                pot_thickness, pot_scale)

    # Shade smooth
    select_only(container)
    bpy.ops.object.shade_smooth()

    # --- Container material assignment ---
    asset_seed = int_hash((seed, 0))
    seed_all(asset_seed)

    make_fn = weighted_sample(CUP_REGISTRY)
    container_mat = make_fn()
    container.data.materials.append(container_mat)

    scratch_prob = 0.5
    edge_wear_prob = 0.5
    if np.random.uniform() <= scratch_prob:
        apply_scratches(container)
    if np.random.uniform() <= edge_wear_prob:
        apply_edge_wear(container)

    # --- Fruit scatter ---
    sel_idx, centers_tmp, _, _ = get_inner_lower_faces(container, lower_thresh=0.80)
    if len(sel_idx) > 0:
        inner_r = np.sqrt(centers_tmp[sel_idx, 0] ** 2 + centers_tmp[sel_idx, 1] ** 2)
        inner_radius = np.percentile(inner_r, 80)
    else:
        inner_radius = 0.05
    np.random.seed(fruit_seed)
    fruit_scale = inner_radius * uniform(0.30, 0.45)

    fruit_copies = scatter_fruits(container, n_fruits, fruit_scale,
                                   scale_rand, fruit_seed)

    # Join all into one object (keeps material slots from each piece)
    all_objs = [container] + fruit_copies
    if len(all_objs) > 1:
        result = join_objects(all_objs)
    else:
        result = container

    result.name = "FruitContainerFactory"
    return result


build(SEED)
