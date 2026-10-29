# [FL_INDEX: keywords="blender_factory, procedural_3d, TableTopFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: TableTopFactory | Category: factories_tex
# Prompt: A 3D model of an isolated tabletop surface rendered from an elevated three-quarter perspective, featuring a rounded-square (squircle) shape with smooth convex edges and a slight uniform thickness, presented without any legs or supporting structure.

import os
import math
import random
import colorsys

import bpy
import numpy as np
from numpy.random import uniform

# --- Inlined material library (hand-crafted for TableTopFactory) ---
# Sources translated faithfully from:

def seed_all(seed: int):
    np.random.seed(seed)
    random.seed(seed)

def _log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _clip_gaussian(mean, std, lo, hi, max_tries=20):
    for _ in range(max_tries):
        val = np.random.normal(mean, std)
        if lo <= val <= hi:
            return float(val)
    return float(np.clip(np.random.normal(mean, std), lo, hi))

def hsv2rgba(h, s, v):
    h = h % 1.0
    s = max(0.0, min(1.0, float(s)))
    v = max(0.0, min(1.0, float(v)))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def _srgb_to_linear(c):
    if c < 0: return 0.0
    elif c < 0.04045: return c / 12.92
    else: return ((c + 0.055) / 1.055) ** 2.4

def hex2rgba(hexval):
    """Hex int to linear RGBA (with sRGB-to-linear,"""

    r = ((hexval >> 16) & 0xFF) / 255.0
    g = ((hexval >> 8) & 0xFF) / 255.0
    b = (hexval & 0xFF) / 255.0
    return (_srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b), 1.0)

def rgb2hsv(rgb):
    r, g, b = rgb[:3]
    return colorsys.rgb_to_hsv(r, g, b)

WOOD_COLORS = [
    0x4C2F27, 0x69432D, 0x371803, 0x7F4040, 0xCC9576, 0x9E8170,
    0x3D2B1F, 0x8D6A58, 0x8B3325, 0x79443C, 0x88540B, 0x9B5F43,
    0x4E3828, 0x4E3828, 0xC09A6B, 0x944536, 0x3F0110, 0x773C12,
    0x6E4E37, 0x5C4033, 0x5C4033, 0x3C3034, 0x96704C, 0x371B1A,
    0x483B32, 0x43141A, 0x471713, 0xC3B090, 0x6B4423, 0x674D46,
    0x5D2E1A, 0x331C1F, 0x7A5640, 0xB99984, 0x71543D, 0x8F4B28,
    0x491A00, 0x836446, 0x7F461B, 0x6A3208, 0x724115, 0xA0522B,
    0x832A0C, 0x371B1A, 0xC7A373, 0x483B32, 0x635147, 0x664228,
    0x5C5248,
]

def bark_hsv():
    hexval = np.random.choice(WOOD_COLORS)
    return rgb2hsv(hex2rgba(hexval)[:3])

def weighted_sample(registry):
    classes, weights = zip(*registry)
    weights = np.array(weights, dtype=float)
    return classes[int(np.random.choice(len(classes), p=weights / weights.sum()))]

def _new_material(name):
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
        "Transmission Weight": ("Transmission Weight", "Transmission"),
    }
    for key, val in kw.items():
        names = aliases.get(key, (key,))
        for name in names:
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = val
                break

def _noise_fac_output(noise_node):
    if "Fac" in noise_node.outputs:
        return noise_node.outputs["Fac"]
    if "Factor" in noise_node.outputs:
        return noise_node.outputs["Factor"]
    return noise_node.outputs[0]

def _connect_output(nt, bsdf, displacement=None, volume=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    if volume is not None:
        nt.links.new(volume, out.inputs["Volume"])
    return out

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

# --------------------------------------------------------------------------
# Marble shader (ceramic/marble.py:shader_marble)
# --------------------------------------------------------------------------
def make_marble(name="Marble"):
    """Faithful raw-bpy port of shader_marble.

    Uses 4D NoiseTexture (substituting MusgraveTexture where needed) + Voronoi
    distance-to-edge for vein pattern. Color ramp mixes white marble with dark
    brown veins. Low roughness (0.1), moderate specular (0.6).
    """

    mat = _new_material(name)
    nt = mat.node_tree

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # Scale (VectorMath SCALE)
    scale_node = nt.nodes.new("ShaderNodeVectorMath")
    scale_node.operation = "SCALE"
    nt.links.new(tex_coord.outputs["Object"], scale_node.inputs[0])
    # default scale = 1.0

    # VectorRotate (Euler XYZ) — no rotation by default
    vec_rotate = nt.nodes.new("ShaderNodeVectorRotate")
    vec_rotate.rotation_type = "EULER_XYZ"
    nt.links.new(scale_node.outputs["Vector"], vec_rotate.inputs["Vector"])

    # Seed value = 0
    seed_val = nt.nodes.new("ShaderNodeValue")
    seed_val.outputs[0].default_value = 0.0

    # Scale value = 3
    scale_val = nt.nodes.new("ShaderNodeValue")
    scale_val.outputs[0].default_value = 3.0

    # add = scale + 1 = 4
    add_node = nt.nodes.new("ShaderNodeMath")
    add_node.inputs[1].default_value = 1.0
    nt.links.new(scale_val.outputs[0], add_node.inputs[0])

    # noise_texture_2: 4D noise, scale=add, detail=15, W=seed
    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise2, "noise_dimensions"):
        try:
            noise2.noise_dimensions = "4D"
        except TypeError:
            pass
    noise2.inputs["Detail"].default_value = 15.0
    nt.links.new(vec_rotate.outputs["Vector"], noise2.inputs["Vector"])
    nt.links.new(seed_val.outputs[0], noise2.inputs["W"])
    nt.links.new(add_node.outputs[0], noise2.inputs["Scale"])

    # map_range: Fac -> [0.48, 0.60] -> [0, 1]
    map_range_1 = nt.nodes.new("ShaderNodeMapRange")
    map_range_1.inputs[1].default_value = 0.48
    map_range_1.inputs[2].default_value = 0.60
    nt.links.new(_noise_fac_output(noise2), map_range_1.inputs["Value"])

    # noise_texture: 4D noise, scale=scale_val(3), detail=15, W=seed
    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise1, "noise_dimensions"):
        try:
            noise1.noise_dimensions = "4D"
        except TypeError:
            pass
    noise1.inputs["Detail"].default_value = 15.0
    nt.links.new(vec_rotate.outputs["Vector"], noise1.inputs["Vector"])
    nt.links.new(seed_val.outputs[0], noise1.inputs["W"])
    nt.links.new(scale_val.outputs[0], noise1.inputs["Scale"])

    # noise_texture_3: 3D noise, Vector=noise1.Fac, scale=8, detail=15
    noise3 = nt.nodes.new("ShaderNodeTexNoise")
    noise3.inputs["Scale"].default_value = 8.0
    noise3.inputs["Detail"].default_value = 15.0
    nt.links.new(_noise_fac_output(noise1), noise3.inputs["Vector"])

    # voronoi_texture: 4D, DISTANCE_TO_EDGE, Vector=noise3.Fac, W=1.64, scale=3
    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(voronoi, "voronoi_dimensions"):
        try:
            voronoi.voronoi_dimensions = "4D"
        except TypeError:
            voronoi.voronoi_dimensions = "3D"
    if hasattr(voronoi, "feature"):
        try:
            voronoi.feature = "DISTANCE_TO_EDGE"
        except TypeError:
            pass
    voronoi.inputs["Scale"].default_value = 3.0
    if "W" in voronoi.inputs:
        voronoi.inputs["W"].default_value = 1.64
    nt.links.new(_noise_fac_output(noise3), voronoi.inputs["Vector"])

    # colorramp_1: Distance -> black veins
    colorramp_1 = nt.nodes.new("ShaderNodeValToRGB")
    colorramp_1.color_ramp.elements[0].position = 0.0
    colorramp_1.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    colorramp_1.color_ramp.elements[1].position = 0.03
    colorramp_1.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
    dist_out = voronoi.outputs.get("Distance") or voronoi.outputs[0]
    nt.links.new(dist_out, colorramp_1.inputs["Fac"])

    # multiply: map_range * colorramp_1
    mul_node = nt.nodes.new("ShaderNodeMath")
    mul_node.operation = "MULTIPLY"
    nt.links.new(map_range_1.outputs["Result"], mul_node.inputs[0])
    nt.links.new(colorramp_1.outputs["Color"], mul_node.inputs[1])

    # noise_texture_1: 4D noise, Vector=noise1.Fac, W=seed, scale=8, detail=15
    noise4 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise4, "noise_dimensions"):
        try:
            noise4.noise_dimensions = "4D"
        except TypeError:
            pass
    noise4.inputs["Scale"].default_value = 8.0
    noise4.inputs["Detail"].default_value = 15.0
    nt.links.new(_noise_fac_output(noise1), noise4.inputs["Vector"])
    nt.links.new(seed_val.outputs[0], noise4.inputs["W"])

    # mix_1: factor=0.8, A=noise1.Fac, B=noise4.Fac
    mix_1 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_1, "data_type"):
        mix_1.data_type = "RGBA"
    mix_1.inputs[0].default_value = 0.8
    nt.links.new(_noise_fac_output(noise1), mix_1.inputs[6])
    nt.links.new(_noise_fac_output(noise4), mix_1.inputs[7])

    # colorramp: Fac -> [0.3 white, 0.9 black]
    colorramp_2 = nt.nodes.new("ShaderNodeValToRGB")
    colorramp_2.color_ramp.elements[0].position = 0.3
    colorramp_2.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    colorramp_2.color_ramp.elements[1].position = 0.9
    colorramp_2.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
    nt.links.new(mix_1.outputs[2], colorramp_2.inputs["Fac"])

    # mix: factor=multiply, A=colorramp, B=dark brown (0.0376, 0.0179, 0.0033)
    mix_2 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_2, "data_type"):
        mix_2.data_type = "RGBA"
    nt.links.new(mul_node.outputs[0], mix_2.inputs[0])
    nt.links.new(colorramp_2.outputs["Color"], mix_2.inputs[6])
    mix_2.inputs[7].default_value = (0.0376, 0.0179, 0.0033, 1.0)

    # Displacement: Height=multiply, Midlevel=0, Scale=0.02
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.02
    nt.links.new(mul_node.outputs[0], disp.inputs["Height"])

    # Principled BSDF: Base Color=mix_1 result, Specular=0.6, Roughness=0.1
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Specular IOR Level": 0.6, "Roughness": 0.1})
    nt.links.new(mix_1.outputs[2], bsdf.inputs["Base Color"])

    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# --------------------------------------------------------------------------
# Wood shader (wood/wood.py:shader_wood)
# MusgraveTexture removed in Blender 5.0 -> substituted with NoiseTexture
# --------------------------------------------------------------------------
def make_wood(name="Wood", color=None):
    """Faithful raw-bpy port of shader_wood.

    MusgraveTexture is replaced with NoiseTexture (Detail→15, varying dimensions
    to approximate the musgrave frequency response). The overall pipeline:
    stretched mapping → multi-octave noise grain → color mixing with bark-derived
    base color → float curve roughness → coat weight.
    """

    if color is None:
        h, s, v = bark_hsv()
        color = hsv2rgba(
            h + float(np.random.uniform(-0.0, 0.05)),
            max(0.0, s + float(np.random.uniform(-0.3, 0.2))),
            v * _log_uniform(0.2, 20)
        )

    wood_w = float(uniform(0, 1))

    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # Stretched mapping for wood grain direction
    mapping_stretched = nt.nodes.new("ShaderNodeMapping")
    mapping_stretched.inputs["Scale"].default_value = (5.0, 100.0, 100.0)
    nt.links.new(tex_coord.outputs["Object"], mapping_stretched.inputs["Vector"])

    # musgrave_texture_2 substitute: 4D noise, stretched mapping, scale=10, detail=15
    musgrave_sub_2 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(musgrave_sub_2, "noise_dimensions"):
        try:
            musgrave_sub_2.noise_dimensions = "4D"
        except TypeError:
            pass
    musgrave_sub_2.inputs["Scale"].default_value = 10.0
    musgrave_sub_2.inputs["Detail"].default_value = 15.0
    if "W" in musgrave_sub_2.inputs:
        musgrave_sub_2.inputs["W"].default_value = wood_w
    nt.links.new(mapping_stretched.outputs["Vector"], musgrave_sub_2.inputs["Vector"])

    # map_range_2: Value -> [0..1] remapped to [1..-1]
    map_range_2 = nt.nodes.new("ShaderNodeMapRange")
    map_range_2.inputs[3].default_value = 1.0
    map_range_2.inputs[4].default_value = -1.0
    nt.links.new(_noise_fac_output(musgrave_sub_2), map_range_2.inputs["Value"])

    # mapping_1: Object coords, no stretch
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tex_coord.outputs["Object"], mapping_1.inputs["Vector"])

    # noise_texture_1: 4D, scale=0.5, detail=1, distortion=1.1, W=w
    noise_1 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise_1, "noise_dimensions"):
        try:
            noise_1.noise_dimensions = "4D"
        except TypeError:
            pass
    noise_1.inputs["Scale"].default_value = 0.5
    noise_1.inputs["Detail"].default_value = 1.0
    if "Distortion" in noise_1.inputs:
        noise_1.inputs["Distortion"].default_value = 1.1
    if "W" in noise_1.inputs:
        noise_1.inputs["W"].default_value = wood_w
    nt.links.new(mapping_1.outputs["Vector"], noise_1.inputs["Vector"])

    # musgrave_texture_1 substitute: 4D noise, Scale=noise1.Fac, detail=15, W=w
    musgrave_sub_1 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(musgrave_sub_1, "noise_dimensions"):
        try:
            musgrave_sub_1.noise_dimensions = "4D"
        except TypeError:
            pass
    musgrave_sub_1.inputs["Detail"].default_value = 15.0
    if "Roughness" in musgrave_sub_1.inputs:
        musgrave_sub_1.inputs["Roughness"].default_value = 0.2
    if "W" in musgrave_sub_1.inputs:
        musgrave_sub_1.inputs["W"].default_value = wood_w
    nt.links.new(_noise_fac_output(noise_1), musgrave_sub_1.inputs["Scale"])

    # map_range: Value -> [0..1] remapped to [-1.4..1.5]
    map_range_a = nt.nodes.new("ShaderNodeMapRange")
    map_range_a.inputs[3].default_value = -1.4
    map_range_a.inputs[4].default_value = 1.5
    nt.links.new(_noise_fac_output(musgrave_sub_1), map_range_a.inputs["Value"])

    # map_range_1: Result -> [0..1] remapped to [1.0..0.5]
    map_range_b = nt.nodes.new("ShaderNodeMapRange")
    map_range_b.inputs[3].default_value = 1.0
    map_range_b.inputs[4].default_value = 0.5
    nt.links.new(map_range_a.outputs["Result"], map_range_b.inputs["Value"])

    # mapping: Object with scale (0.15, 1.0, 0.15)
    mapping_ring = nt.nodes.new("ShaderNodeMapping")
    mapping_ring.inputs["Scale"].default_value = (0.15, 1.0, 0.15)
    nt.links.new(tex_coord.outputs["Object"], mapping_ring.inputs["Vector"])

    # noise_texture: 4D, detail=5, distortion=1, W=w
    noise_ring = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise_ring, "noise_dimensions"):
        try:
            noise_ring.noise_dimensions = "4D"
        except TypeError:
            pass
    noise_ring.inputs["Detail"].default_value = 5.0
    if "Distortion" in noise_ring.inputs:
        noise_ring.inputs["Distortion"].default_value = 1.0
    if "W" in noise_ring.inputs:
        noise_ring.inputs["W"].default_value = wood_w
    nt.links.new(mapping_ring.outputs["Vector"], noise_ring.inputs["Vector"])

    # musgrave_texture substitute: 4D noise, Vector=noise_ring.Fac, scale=4, detail=10, W=w
    musgrave_sub_0 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(musgrave_sub_0, "noise_dimensions"):
        try:
            musgrave_sub_0.noise_dimensions = "4D"
        except TypeError:
            pass
    musgrave_sub_0.inputs["Scale"].default_value = 4.0
    musgrave_sub_0.inputs["Detail"].default_value = 10.0
    if "W" in musgrave_sub_0.inputs:
        musgrave_sub_0.inputs["W"].default_value = wood_w
    nt.links.new(_noise_fac_output(noise_ring), musgrave_sub_0.inputs["Vector"])

    # mix: A=noise_ring.Fac, B=musgrave_sub_0.Fac (factor default 0.5)
    mix_a = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_a, "data_type"):
        mix_a.data_type = "RGBA"
    nt.links.new(_noise_fac_output(noise_ring), mix_a.inputs[6])
    nt.links.new(_noise_fac_output(musgrave_sub_0), mix_a.inputs[7])

    # mix_1: MULTIPLY, factor=0.9, A=map_range_b.Result, B=mix_a
    mix_b = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_b, "data_type"):
        mix_b.data_type = "RGBA"
    mix_b.blend_type = "MULTIPLY"
    mix_b.inputs[0].default_value = 0.9
    nt.links.new(map_range_b.outputs["Result"], mix_b.inputs[6])
    nt.links.new(mix_a.outputs[2], mix_b.inputs[7])

    # mix_2: MULTIPLY, factor=0.95, A=map_range_2.Result, B=mix_b
    mix_c = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_c, "data_type"):
        mix_c.data_type = "RGBA"
    mix_c.blend_type = "MULTIPLY"
    mix_c.inputs[0].default_value = 0.95
    nt.links.new(map_range_2.outputs["Result"], mix_c.inputs[6])
    nt.links.new(mix_b.outputs[2], mix_c.inputs[7])

    # hue_saturation_value: Saturation=0.8, Value=0.2, Color=color
    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Saturation"].default_value = 0.8
    hsv_node.inputs["Value"].default_value = 0.2
    hsv_node.inputs["Color"].default_value = color

    # mix_3: factor=mix_c, A=hsv_node, B=color
    mix_d = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_d, "data_type"):
        mix_d.data_type = "RGBA"
    nt.links.new(mix_c.outputs[2], mix_d.inputs[0])
    nt.links.new(hsv_node.outputs["Color"], mix_d.inputs[6])
    mix_d.inputs[7].default_value = color

    # Displacement: Height = mix_c * log_uniform(0.0002, 0.01)
    disp_scale = _log_uniform(0.0002, 0.01)
    mul_disp = nt.nodes.new("ShaderNodeMath")
    mul_disp.operation = "MULTIPLY"
    mul_disp.inputs[1].default_value = disp_scale
    nt.links.new(mix_c.outputs[2], mul_disp.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_disp.outputs[0], disp.inputs["Height"])

    # Roughness: float curve from noise, base_rough -> base_rough + variation
    base_rough = float(np.random.uniform(0.0, 0.4))
    rough_var = float(np.random.uniform(0.0, 0.8))
    noise_rough = nt.nodes.new("ShaderNodeTexNoise")
    noise_rough.inputs["Scale"].default_value = _log_uniform(40, 50)
    fc = _build_float_curve(nt, _noise_fac_output(noise_rough),
                            [(0, base_rough), (1, base_rough + rough_var)])

    # Principled BSDF with Coat Weight
    coat_weight = float(np.clip(np.random.uniform(0, 1.4), 0, 1))
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Coat Weight": coat_weight})
    nt.links.new(mix_d.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])

    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# --------------------------------------------------------------------------
# TiledWood shader (wood/tiled_wood.py:shader_wood_tiled)
# MusgraveTexture removed in Blender 5.0 -> substituted with NoiseTexture
# --------------------------------------------------------------------------
def make_tiled_wood(name="TiledWood"):
    """Faithful raw-bpy port of shader_wood_tiled + nodegroup_tiled_wood + nodegroup_tiling.

    Brick texture tiles the surface; per-tile seed offsets drive 4D noise wood
    grain. Multiple noise layers (substituting musgrave) create the wood ring
    and detail patterns. Final color mixes with tile mortar lines.
    """
    # Sample parameters per original code
    hscale = _clip_gaussian(6, 4, 3, 9)
    vscale = float(uniform(0.05, 0.2)) * hscale
    tiled_seed = float(uniform(-1000.0, 1000.0))

    # Base color from wood.get_color()
    h, s, v = bark_hsv()
    base_color = hsv2rgba(
        h + float(np.random.uniform(-0.0, 0.05)),
        max(0.0, s + float(np.random.uniform(-0.3, 0.2))),
        v * _log_uniform(0.2, 20)
    )

    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # === Tiling nodegroup (inlined) ===
    # 1/hscale
    div_h = nt.nodes.new("ShaderNodeMath")
    div_h.operation = "DIVIDE"
    div_h.inputs[0].default_value = 1.0
    div_h.inputs[1].default_value = hscale

    # multiply by default factor
    mul_offset = nt.nodes.new("ShaderNodeMath")
    mul_offset.operation = "MULTIPLY"
    nt.links.new(div_h.outputs[0], mul_offset.inputs[0])
    mul_offset.inputs[1].default_value = 1.0

    # CombineXYZ for offset: Y=mul_offset
    offset_vec = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(mul_offset.outputs[0], offset_vec.inputs["Y"])

    # Mapping with random translation (matching `uniform(0,1,3)`)
    mapping_rand = nt.nodes.new("ShaderNodeMapping")
    rand_translation = (float(uniform(0, 1)), float(uniform(0, 1)), float(uniform(0, 1)))
    mapping_rand.inputs["Location"].default_value = rand_translation
    nt.links.new(tex_coord.outputs["Object"], mapping_rand.inputs["Vector"])

    # Add offset
    add_offset = nt.nodes.new("ShaderNodeVectorMath")
    nt.links.new(mapping_rand.outputs["Vector"], add_offset.inputs[0])
    nt.links.new(offset_vec.outputs[0], add_offset.inputs[1])

    # 1/vscale
    div_v = nt.nodes.new("ShaderNodeMath")
    div_v.operation = "DIVIDE"
    div_v.inputs[0].default_value = 1.0
    div_v.inputs[1].default_value = vscale

    # BrickTexture
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.inputs["Color2"].default_value = (0.0, 0.0, 0.0, 1.0)
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Mortar Size"].default_value = 0.005
    brick.inputs["Mortar Smooth"].default_value = 1.0
    brick.inputs["Bias"].default_value = -0.5
    if hasattr(brick, "squash_frequency"):
        brick.squash_frequency = 1
    nt.links.new(add_offset.outputs["Vector"], brick.inputs["Vector"])
    nt.links.new(div_v.outputs[0], brick.inputs["Brick Width"])
    nt.links.new(div_h.outputs[0], brick.inputs["Row Height"])

    # multiply_add: brick.Color * 1000 + tiled_seed -> per-tile seed
    mul_add = nt.nodes.new("ShaderNodeMath")
    mul_add.operation = "MULTIPLY_ADD"
    mul_add.inputs[1].default_value = 1000.0
    mul_add.inputs[2].default_value = tiled_seed
    nt.links.new(brick.outputs["Color"], mul_add.inputs[0])

    # === TiledWood nodegroup (inlined) ===
    # Stretched mapping
    mapping_stretched = nt.nodes.new("ShaderNodeMapping")
    mapping_stretched.inputs["Scale"].default_value = (5.0, 100.0, 100.0)
    nt.links.new(tex_coord.outputs["Object"], mapping_stretched.inputs["Vector"])

    # musgrave_texture_2 substitute: 4D noise on stretched mapping, W=per-tile seed
    musgrave_sub_2 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(musgrave_sub_2, "noise_dimensions"):
        try:
            musgrave_sub_2.noise_dimensions = "4D"
        except TypeError:
            pass
    musgrave_sub_2.inputs["Scale"].default_value = 10.0
    musgrave_sub_2.inputs["Detail"].default_value = 15.0
    nt.links.new(mapping_stretched.outputs["Vector"], musgrave_sub_2.inputs["Vector"])
    nt.links.new(mul_add.outputs[0], musgrave_sub_2.inputs["W"])

    # map_range_2: [0..1] -> [1..-1]
    map_range_2 = nt.nodes.new("ShaderNodeMapRange")
    map_range_2.inputs[3].default_value = 1.0
    map_range_2.inputs[4].default_value = -1.0
    nt.links.new(_noise_fac_output(musgrave_sub_2), map_range_2.inputs["Value"])

    # mapping_1: Object, no stretch
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tex_coord.outputs["Object"], mapping_1.inputs["Vector"])

    # noise_texture_1: 4D, scale=0.5, detail=1, distortion=1.1, W=per-tile seed
    noise_1 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise_1, "noise_dimensions"):
        try:
            noise_1.noise_dimensions = "4D"
        except TypeError:
            pass
    noise_1.inputs["Scale"].default_value = 0.5
    noise_1.inputs["Detail"].default_value = 1.0
    if "Distortion" in noise_1.inputs:
        noise_1.inputs["Distortion"].default_value = 1.1
    nt.links.new(mapping_1.outputs["Vector"], noise_1.inputs["Vector"])
    nt.links.new(mul_add.outputs[0], noise_1.inputs["W"])

    # musgrave_texture_1 substitute: 4D noise, Scale=noise1.Fac, detail=15, W=per-tile seed
    musgrave_sub_1 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(musgrave_sub_1, "noise_dimensions"):
        try:
            musgrave_sub_1.noise_dimensions = "4D"
        except TypeError:
            pass
    musgrave_sub_1.inputs["Detail"].default_value = 15.0
    if "Roughness" in musgrave_sub_1.inputs:
        musgrave_sub_1.inputs["Roughness"].default_value = 0.2
    nt.links.new(_noise_fac_output(noise_1), musgrave_sub_1.inputs["Scale"])
    nt.links.new(mul_add.outputs[0], musgrave_sub_1.inputs["W"])

    # map_range: [0..1] -> [-1.4..1.5]
    map_range_a = nt.nodes.new("ShaderNodeMapRange")
    map_range_a.inputs[3].default_value = -1.4
    map_range_a.inputs[4].default_value = 1.5
    nt.links.new(_noise_fac_output(musgrave_sub_1), map_range_a.inputs["Value"])

    # map_range_1: Result -> [1.0..0.5]
    map_range_b = nt.nodes.new("ShaderNodeMapRange")
    map_range_b.inputs[3].default_value = 1.0
    map_range_b.inputs[4].default_value = 0.5
    nt.links.new(map_range_a.outputs["Result"], map_range_b.inputs["Value"])

    # mapping: Object with (0.15, 1.0, 0.15)
    mapping_ring = nt.nodes.new("ShaderNodeMapping")
    mapping_ring.inputs["Scale"].default_value = (0.15, 1.0, 0.15)
    nt.links.new(tex_coord.outputs["Object"], mapping_ring.inputs["Vector"])

    # noise_texture: 4D, detail=5, distortion=1, W=per-tile seed
    noise_ring = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise_ring, "noise_dimensions"):
        try:
            noise_ring.noise_dimensions = "4D"
        except TypeError:
            pass
    noise_ring.inputs["Detail"].default_value = 5.0
    if "Distortion" in noise_ring.inputs:
        noise_ring.inputs["Distortion"].default_value = 1.0
    nt.links.new(mapping_ring.outputs["Vector"], noise_ring.inputs["Vector"])
    nt.links.new(mul_add.outputs[0], noise_ring.inputs["W"])

    # musgrave_texture substitute: 4D noise, Vector=noise_ring.Fac, scale=4, detail=10
    musgrave_sub_0 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(musgrave_sub_0, "noise_dimensions"):
        try:
            musgrave_sub_0.noise_dimensions = "4D"
        except TypeError:
            pass
    musgrave_sub_0.inputs["Scale"].default_value = 4.0
    musgrave_sub_0.inputs["Detail"].default_value = 10.0
    nt.links.new(_noise_fac_output(noise_ring), musgrave_sub_0.inputs["Vector"])
    nt.links.new(mul_add.outputs[0], musgrave_sub_0.inputs["W"])

    # mix: A=noise_ring.Fac, B=musgrave_sub_0.Fac
    mix_a = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_a, "data_type"):
        mix_a.data_type = "RGBA"
    nt.links.new(_noise_fac_output(noise_ring), mix_a.inputs[6])
    nt.links.new(_noise_fac_output(musgrave_sub_0), mix_a.inputs[7])

    # mix_1: MULTIPLY, factor=0.9, A=map_range_b.Result, B=mix_a
    mix_b = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_b, "data_type"):
        mix_b.data_type = "RGBA"
    mix_b.blend_type = "MULTIPLY"
    mix_b.inputs[0].default_value = 0.9
    nt.links.new(map_range_b.outputs["Result"], mix_b.inputs[6])
    nt.links.new(mix_a.outputs[2], mix_b.inputs[7])

    # mix_2: MULTIPLY, factor=0.95, A=map_range_2.Result, B=mix_b
    mix_c = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_c, "data_type"):
        mix_c.data_type = "RGBA"
    mix_c.blend_type = "MULTIPLY"
    mix_c.inputs[0].default_value = 0.95
    nt.links.new(map_range_2.outputs["Result"], mix_c.inputs[6])
    nt.links.new(mix_b.outputs[2], mix_c.inputs[7])

    # hue_saturation_value: Saturation=0.8, Value=0.2, Fac=0, Color=base_color
    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Saturation"].default_value = 0.8
    hsv_node.inputs["Value"].default_value = 0.2
    hsv_node.inputs["Fac"].default_value = 0.0
    hsv_node.inputs["Color"].default_value = base_color

    # mix_3: factor=mix_c, A=hsv_node, B=base_color
    mix_d = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_d, "data_type"):
        mix_d.data_type = "RGBA"
    nt.links.new(mix_c.outputs[2], mix_d.inputs[0])
    nt.links.new(hsv_node.outputs["Color"], mix_d.inputs[6])
    mix_d.inputs[7].default_value = base_color

    # mix_4: MULTIPLY, factor=1.0, A=mix_d, B=brick.Color (tile color)
    mix_e = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_e, "data_type"):
        mix_e.data_type = "RGBA"
    mix_e.blend_type = "MULTIPLY"
    mix_e.inputs[0].default_value = 1.0
    nt.links.new(mix_d.outputs[2], mix_e.inputs[6])
    nt.links.new(brick.outputs["Color"], mix_e.inputs[7])

    final_color = mix_e.outputs[2]

    # Roughness: float curve from color
    rough_lo = float(uniform(0.3, 0.5))
    rough_hi = float(uniform(0.8, 1.0))
    fc = _build_float_curve(nt, final_color, [(0, rough_lo), (1, rough_hi)])

    # Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(final_color, bsdf.inputs["Base Color"])
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])

    # Displacement: (brick.Color + mix_c * 0.1) * 0.01
    mul_detail = nt.nodes.new("ShaderNodeMath")
    mul_detail.operation = "MULTIPLY"
    mul_detail.inputs[1].default_value = 0.1
    nt.links.new(mix_c.outputs[2], mul_detail.inputs[0])

    add_disp = nt.nodes.new("ShaderNodeMath")
    nt.links.new(brick.outputs["Color"], add_disp.inputs[0])
    nt.links.new(mul_detail.outputs[0], add_disp.inputs[1])

    mul_disp = nt.nodes.new("ShaderNodeMath")
    mul_disp.operation = "MULTIPLY"
    mul_disp.inputs[1].default_value = 0.01
    nt.links.new(add_disp.outputs[0], mul_disp.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_disp.outputs[0], disp.inputs["Height"])

    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# --------------------------------------------------------------------------
# PlasticRough shader (plastic/plastic_rough.py:shader_rough_plastic)
# --------------------------------------------------------------------------
def make_plastic_rough(name="PlasticRough"):
    """Faithful raw-bpy port of shader_rough_plastic + nodegroup_plastics."""

    roughness_param = float(uniform(0.0, 1.0))
    seed_param = float(uniform(-1000.0, 1000.0))
    base_color = hsv2rgba(
        float(uniform(0, 1)),
        float(uniform(0.5, 0.8)),
        _log_uniform(0.01, 0.5)
    )

    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # MapRange: roughness -> [0.05, 0.25]
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs["Value"].default_value = roughness_param
    map_range.inputs[3].default_value = 0.05
    map_range.inputs[4].default_value = 0.25

    # Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Base Color": base_color})
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])

    # Noise: scale = 1.0 * 2000 = 2000, 4D, detail=15, distortion=2, W=seed
    noise = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise, "noise_dimensions"):
        try:
            noise.noise_dimensions = "4D"
        except TypeError:
            pass
    noise.inputs["Scale"].default_value = 2000.0
    noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = seed_param
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    # multiply_1: maprange.Result * 0.4
    mul_1 = nt.nodes.new("ShaderNodeMath")
    mul_1.operation = "MULTIPLY"
    mul_1.inputs[1].default_value = 0.4
    nt.links.new(map_range.outputs["Result"], mul_1.inputs[0])

    # multiply_2: noise.Fac * mul_1
    mul_2 = nt.nodes.new("ShaderNodeMath")
    mul_2.operation = "MULTIPLY"
    nt.links.new(_noise_fac_output(noise), mul_2.inputs[0])
    nt.links.new(mul_1.outputs[0], mul_2.inputs[1])

    # multiply_3: mul_2 * 0.003
    mul_3 = nt.nodes.new("ShaderNodeMath")
    mul_3.operation = "MULTIPLY"
    mul_3.inputs[1].default_value = 0.003
    nt.links.new(mul_2.outputs[0], mul_3.inputs[0])

    # Displacement
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_3.outputs[0], disp.inputs["Height"])

    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# --------------------------------------------------------------------------
# GlassVolume shader (ceramic/glass_volume.py:shader_glass_volume)
# --------------------------------------------------------------------------
def make_glass_volume(name="GlassVolume"):
    """Faithful raw-bpy port of shader_glass_volume."""

    if float(uniform(0, 1)) < 0.3:
        glass_color = (1.0, 1.0, 1.0, 1.0)
    else:
        glass_color = hsv2rgba(
            float(uniform(0, 1)),
            float(uniform(0.5, 0.9)),
            float(uniform(0.6, 0.9))
        )
    density = 100.0

    mat = _new_material(name)
    nt = mat.node_tree

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=0.0, **{"Transmission Weight": 1.0})

    vol_abs = nt.nodes.new("ShaderNodeVolumeAbsorption")
    vol_abs.inputs["Color"].default_value = glass_color
    vol_abs.inputs["Density"].default_value = density

    _connect_output(nt, bsdf, volume=vol_abs.outputs[0])
    return mat

# --- Material registry (mirrors material_assignments.table_top) ---
# table_top = [
#     (ceramic.Marble, 1.0),
#     (wood.TiledWood, 1.0),
#     (wood.Wood, 1.0),
#     (plastic.PlasticRough, 0.5),
#     (ceramic.GlassVolume, 1.0),
# ]
TABLE_TOP_REGISTRY = [
    (make_marble,        1.0),
    (make_tiled_wood,    1.0),
    (make_wood,          1.0),
    (make_plastic_rough, 0.5),
    (make_glass_volume,  1.0),
]

def get_material(registry, name="TableTopMaterial"):
    make_fn = weighted_sample(registry)
    return make_fn(name=name)

# ── Seed ──
SEED = int(os.environ.get("SEED", 0))
random.seed(SEED)
np.random.seed(SEED)

# ── Scene cleanup ──
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
for mesh in list(bpy.data.meshes):
    bpy.data.meshes.remove(mesh)
for ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(ng)
for mat in list(bpy.data.materials):
    bpy.data.materials.remove(mat)
bpy.context.scene.cursor.location = (0, 0, 0)

# TableTopFactory itself has no get_material_params(), but when used by
# DiningTableFactory etc., it gets material from material_assignments.table_top.
# We sample that registry directly.
seed_all(SEED)
MAT_TOP = get_material(TABLE_TOP_REGISTRY, "TableTopMaterial")

# wear_tear probability gates — TableTopFactory and DiningTableFactory both have
# finalize_assets commented out / absent, so wear_tear is not applied. But we
# consume the RNG state to maintain alignment.
WEAR_DO_SCRATCH = np.random.uniform() <= 0.5
WEAR_DO_EDGEWEAR = np.random.uniform() <= 0.5

# --- Original geometry helpers (copied verbatim from objects_blender/tables/
#     TableTopFactory.py) ====================================================

def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def new_link(tree, from_socket, to_socket):
    tree.links.new(from_socket, to_socket)

def set_fillet_mode(node, mode):
    """Handle Blender 5.0 FilletCurve mode change: property -> Menu socket."""

    try:
        node.mode = mode
    except AttributeError:
        pass
    for inp in node.inputs:
        if inp.bl_idname == "NodeSocketMenu" or inp.name == "Mode":
            try:
                inp.default_value = mode.title()
            except Exception:
                pass
            break

def set_capture_data_type(node, dtype):
    """Configure CaptureAttribute data type for Blender 5.0+."""

    if hasattr(node, "capture_items"):
        if len(node.capture_items) == 0:
            node.capture_items.new(dtype, "Value")
        else:
            node.capture_items[0].data_type = dtype
    else:
        try:
            node.data_type = dtype
        except AttributeError:
            pass

def set_sample_curve_all(node):
    """Set use_all_curves on SampleCurve if available."""

    try:
        node.use_all_curves = True
    except AttributeError:
        pass

def build_n_gon_profile():
    ng = bpy.data.node_groups.new("n_gon_profile", "GeometryNodeTree")
    ng.interface.new_socket("Profile N-gon", in_out="INPUT", socket_type="NodeSocketInt")
    ng.interface.new_socket("Profile Width", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Profile Aspect Ratio", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Profile Fillet Ratio", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Output", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    for item in ng.interface.items_tree:
        if hasattr(item, "default_value"):
            if item.name == "Profile N-gon":
                item.default_value = 4
            elif item.name == "Profile Width":
                item.default_value = 1.0
            elif item.name == "Profile Aspect Ratio":
                item.default_value = 1.0
            elif item.name == "Profile Fillet Ratio":
                item.default_value = 0.2

    n = {}
    L = new_link

    n["in"] = ng.nodes.new("NodeGroupInput")
    n["out"] = ng.nodes.new("NodeGroupOutput")

    n["val"] = ng.nodes.new("ShaderNodeValue")
    n["val"].outputs[0].default_value = 0.5

    n["cc"] = ng.nodes.new("GeometryNodeCurvePrimitiveCircle")
    n["cc"].mode = "RADIUS"
    L(ng, n["in"].outputs["Profile N-gon"], n["cc"].inputs["Resolution"])
    L(ng, n["val"].outputs[0], n["cc"].inputs["Radius"])

    n["div"] = ng.nodes.new("ShaderNodeMath")
    n["div"].operation = "DIVIDE"
    n["div"].inputs[0].default_value = math.pi
    L(ng, n["in"].outputs["Profile N-gon"], n["div"].inputs[1])

    n["cz1"] = ng.nodes.new("ShaderNodeCombineXYZ")
    L(ng, n["div"].outputs[0], n["cz1"].inputs["Z"])

    n["t1"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["cc"].outputs["Curve"], n["t1"].inputs["Geometry"])
    L(ng, n["cz1"].outputs[0], n["t1"].inputs["Rotation"])

    n["t2"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["t1"].outputs[0], n["t2"].inputs["Geometry"])
    n["t2"].inputs["Rotation"].default_value = (0, 0, -math.pi / 2)

    n["mul_ar"] = ng.nodes.new("ShaderNodeMath")
    n["mul_ar"].operation = "MULTIPLY"
    L(ng, n["in"].outputs["Profile Aspect Ratio"], n["mul_ar"].inputs[0])
    L(ng, n["in"].outputs["Profile Width"], n["mul_ar"].inputs[1])

    n["cxyz"] = ng.nodes.new("ShaderNodeCombineXYZ")
    L(ng, n["in"].outputs["Profile Width"], n["cxyz"].inputs["X"])
    L(ng, n["mul_ar"].outputs[0], n["cxyz"].inputs["Y"])
    n["cxyz"].inputs["Z"].default_value = 1.0

    n["t3"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["t2"].outputs[0], n["t3"].inputs["Geometry"])
    L(ng, n["cxyz"].outputs[0], n["t3"].inputs["Scale"])

    n["mul_f"] = ng.nodes.new("ShaderNodeMath")
    n["mul_f"].operation = "MULTIPLY"
    L(ng, n["in"].outputs["Profile Width"], n["mul_f"].inputs[0])
    L(ng, n["in"].outputs["Profile Fillet Ratio"], n["mul_f"].inputs[1])

    n["fc"] = ng.nodes.new("GeometryNodeFilletCurve")
    set_fillet_mode(n["fc"], "POLY")
    L(ng, n["t3"].outputs[0], n["fc"].inputs["Curve"])
    n["fc"].inputs["Count"].default_value = 8
    L(ng, n["mul_f"].outputs[0], n["fc"].inputs["Radius"])
    n["fc"].inputs["Limit Radius"].default_value = True

    L(ng, n["fc"].outputs[0], n["out"].inputs["Output"])

    return ng

def build_n_gon_cylinder():
    ng = bpy.data.node_groups.new("n_gon_cylinder", "GeometryNodeTree")
    ng.interface.new_socket("Radius Curve", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Height", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("N-gon", in_out="INPUT", socket_type="NodeSocketInt")
    ng.interface.new_socket("Profile Width", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Aspect Ratio", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Fillet Ratio", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Profile Resolution", in_out="INPUT", socket_type="NodeSocketInt")
    ng.interface.new_socket("Resolution", in_out="INPUT", socket_type="NodeSocketInt")
    ng.interface.new_socket("Mesh", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Profile Curve", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Caps", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    for item in ng.interface.items_tree:
        if hasattr(item, "default_value"):
            if item.name == "Height":
                item.default_value = 0.5
            elif item.name == "Profile Width":
                item.default_value = 0.5
            elif item.name == "Aspect Ratio":
                item.default_value = 0.5
            elif item.name == "Fillet Ratio":
                item.default_value = 0.2
            elif item.name == "Profile Resolution":
                item.default_value = 64
            elif item.name == "Resolution":
                item.default_value = 128

    n = {}
    L = new_link

    n["in"] = ng.nodes.new("NodeGroupInput")
    n["out"] = ng.nodes.new("NodeGroupOutput")

    n["mul_h"] = ng.nodes.new("ShaderNodeMath")
    n["mul_h"].operation = "MULTIPLY"
    L(ng, n["in"].outputs["Height"], n["mul_h"].inputs[0])
    n["mul_h"].inputs[1].default_value = -1.0

    n["cz_h"] = ng.nodes.new("ShaderNodeCombineXYZ")
    L(ng, n["mul_h"].outputs[0], n["cz_h"].inputs["Z"])

    n["cl"] = ng.nodes.new("GeometryNodeCurvePrimitiveLine")
    L(ng, n["cz_h"].outputs[0], n["cl"].inputs["End"])

    n["tilt"] = ng.nodes.new("GeometryNodeSetCurveTilt")
    L(ng, n["cl"].outputs[0], n["tilt"].inputs["Curve"])
    n["tilt"].inputs["Tilt"].default_value = math.pi

    n["rs"] = ng.nodes.new("GeometryNodeResampleCurve")
    L(ng, n["tilt"].outputs[0], n["rs"].inputs["Curve"])
    L(ng, n["in"].outputs["Resolution"], n["rs"].inputs["Count"])

    n["sp"] = ng.nodes.new("GeometryNodeSplineParameter")

    n["cap"] = ng.nodes.new("GeometryNodeCaptureAttribute")
    set_capture_data_type(n["cap"], "FLOAT")
    L(ng, n["rs"].outputs[0], n["cap"].inputs["Geometry"])
    val_input = None
    for inp in n["cap"].inputs:
        if inp.name == "Value" and inp.bl_idname != "NodeSocketGeometry":
            val_input = inp
            break
    if val_input is None:
        val_input = n["cap"].inputs[1]
    L(ng, n["sp"].outputs["Factor"], val_input)

    n["ngp"] = ng.nodes.new("GeometryNodeGroup")
    n["ngp"].node_tree = bpy.data.node_groups["n_gon_profile"]
    L(ng, n["in"].outputs["N-gon"], n["ngp"].inputs["Profile N-gon"])
    L(ng, n["in"].outputs["Profile Width"], n["ngp"].inputs["Profile Width"])
    L(ng, n["in"].outputs["Aspect Ratio"], n["ngp"].inputs["Profile Aspect Ratio"])
    L(ng, n["in"].outputs["Fillet Ratio"], n["ngp"].inputs["Profile Fillet Ratio"])

    n["rs2"] = ng.nodes.new("GeometryNodeResampleCurve")
    L(ng, n["ngp"].outputs[0], n["rs2"].inputs["Curve"])
    L(ng, n["in"].outputs["Profile Resolution"], n["rs2"].inputs["Count"])

    n["c2m"] = ng.nodes.new("GeometryNodeCurveToMesh")
    cap_geo_out = n["cap"].outputs["Geometry"] if "Geometry" in n["cap"].outputs else n["cap"].outputs[0]
    L(ng, cap_geo_out, n["c2m"].inputs["Curve"])
    L(ng, n["rs2"].outputs[0], n["c2m"].inputs["Profile Curve"])
    n["c2m"].inputs["Fill Caps"].default_value = True

    cap_attr_out = None
    for o in n["cap"].outputs:
        if o.name == "Value" and o.bl_idname != "NodeSocketGeometry":
            cap_attr_out = o
            break
    if cap_attr_out is None:
        cap_attr_out = n["cap"].outputs[1]

    n["pos1"] = ng.nodes.new("GeometryNodeInputPosition")
    n["sep1"] = ng.nodes.new("ShaderNodeSeparateXYZ")
    L(ng, n["pos1"].outputs[0], n["sep1"].inputs[0])

    n["sc"] = ng.nodes.new("GeometryNodeSampleCurve")
    set_sample_curve_all(n["sc"])
    L(ng, n["in"].outputs["Radius Curve"], n["sc"].inputs["Curves"])
    L(ng, cap_attr_out, n["sc"].inputs["Factor"])

    n["sep2"] = ng.nodes.new("ShaderNodeSeparateXYZ")
    L(ng, n["sc"].outputs["Position"], n["sep2"].inputs[0])

    n["cxy"] = ng.nodes.new("ShaderNodeCombineXYZ")
    L(ng, n["sep2"].outputs["X"], n["cxy"].inputs["X"])
    L(ng, n["sep2"].outputs["Y"], n["cxy"].inputs["Y"])

    n["len"] = ng.nodes.new("ShaderNodeVectorMath")
    n["len"].operation = "LENGTH"
    L(ng, n["cxy"].outputs[0], n["len"].inputs[0])

    n["mulx"] = ng.nodes.new("ShaderNodeMath")
    n["mulx"].operation = "MULTIPLY"
    L(ng, n["sep1"].outputs["X"], n["mulx"].inputs[0])
    L(ng, n["len"].outputs["Value"], n["mulx"].inputs[1])

    n["muly"] = ng.nodes.new("ShaderNodeMath")
    n["muly"].operation = "MULTIPLY"
    L(ng, n["sep1"].outputs["Y"], n["muly"].inputs[0])
    L(ng, n["len"].outputs["Value"], n["muly"].inputs[1])

    n["pos2"] = ng.nodes.new("GeometryNodeInputPosition")
    n["sep3"] = ng.nodes.new("ShaderNodeSeparateXYZ")
    L(ng, n["pos2"].outputs[0], n["sep3"].inputs[0])

    n["as"] = ng.nodes.new("GeometryNodeAttributeStatistic")
    n["as"].data_type = "FLOAT"
    L(ng, n["in"].outputs["Radius Curve"], n["as"].inputs["Geometry"])
    as_attr_input = None
    for inp in n["as"].inputs:
        if inp.name == "Attribute" and inp.bl_idname == "NodeSocketFloat":
            as_attr_input = inp
            break
    if as_attr_input is None:
        as_attr_input = n["as"].inputs[2]
    L(ng, n["sep3"].outputs["Z"], as_attr_input)

    n["mr"] = ng.nodes.new("ShaderNodeMapRange")
    L(ng, n["sep2"].outputs["Z"], n["mr"].inputs["Value"])
    L(ng, n["as"].outputs["Min"], n["mr"].inputs[1])
    L(ng, n["as"].outputs["Max"], n["mr"].inputs[2])
    L(ng, n["mul_h"].outputs[0], n["mr"].inputs[3])
    n["mr"].inputs[4].default_value = 0.0

    n["cfinal"] = ng.nodes.new("ShaderNodeCombineXYZ")
    L(ng, n["mulx"].outputs[0], n["cfinal"].inputs["X"])
    L(ng, n["muly"].outputs[0], n["cfinal"].inputs["Y"])
    L(ng, n["mr"].outputs["Result"], n["cfinal"].inputs["Z"])

    n["sp2"] = ng.nodes.new("GeometryNodeSetPosition")
    L(ng, n["c2m"].outputs[0], n["sp2"].inputs["Geometry"])
    L(ng, n["cfinal"].outputs[0], n["sp2"].inputs["Position"])

    n["idx"] = ng.nodes.new("GeometryNodeInputIndex")
    n["ds"] = ng.nodes.new("GeometryNodeAttributeDomainSize")
    L(ng, n["c2m"].outputs[0], n["ds"].inputs[0])

    n["sub"] = ng.nodes.new("ShaderNodeMath")
    n["sub"].operation = "SUBTRACT"
    L(ng, n["ds"].outputs["Face Count"], n["sub"].inputs[0])
    n["sub"].inputs[1].default_value = 2.0

    n["lt"] = ng.nodes.new("FunctionNodeCompare")
    n["lt"].data_type = "INT"
    n["lt"].operation = "LESS_THAN"
    L(ng, n["idx"].outputs[0], n["lt"].inputs[2])
    L(ng, n["sub"].outputs[0], n["lt"].inputs[3])

    n["del"] = ng.nodes.new("GeometryNodeDeleteGeometry")
    n["del"].domain = "FACE"
    L(ng, n["c2m"].outputs[0], n["del"].inputs["Geometry"])
    L(ng, n["lt"].outputs[0], n["del"].inputs["Selection"])

    L(ng, n["sp2"].outputs[0], n["out"].inputs["Mesh"])
    L(ng, n["rs2"].outputs[0], n["out"].inputs["Profile Curve"])
    L(ng, n["del"].outputs[0], n["out"].inputs["Caps"])

    return ng

def build_create_cap():
    ng = bpy.data.node_groups.new("create_cap", "GeometryNodeTree")
    ng.interface.new_socket("Radius", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Resolution", in_out="INPUT", socket_type="NodeSocketInt")
    ng.interface.new_socket("Mesh", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    for item in ng.interface.items_tree:
        if hasattr(item, "default_value"):
            if item.name == "Radius":
                item.default_value = 1.0
            elif item.name == "Resolution":
                item.default_value = 64

    n = {}
    L = new_link

    n["in"] = ng.nodes.new("NodeGroupInput")
    n["out"] = ng.nodes.new("NodeGroupOutput")

    n["mul"] = ng.nodes.new("ShaderNodeMath")
    n["mul"].operation = "MULTIPLY"
    L(ng, n["in"].outputs["Radius"], n["mul"].inputs[0])
    n["mul"].inputs[1].default_value = 257.0

    n["uv"] = ng.nodes.new("GeometryNodeMeshUVSphere")
    L(ng, n["in"].outputs["Resolution"], n["uv"].inputs["Segments"])
    L(ng, n["mul"].outputs[0], n["uv"].inputs["Rings"])
    L(ng, n["in"].outputs["Radius"], n["uv"].inputs["Radius"])

    n["pow"] = ng.nodes.new("ShaderNodeMath")
    n["pow"].operation = "POWER"
    L(ng, n["in"].outputs["Radius"], n["pow"].inputs[0])
    n["pow"].inputs[1].default_value = 2.0

    n["sub"] = ng.nodes.new("ShaderNodeMath")
    n["sub"].operation = "SUBTRACT"
    L(ng, n["pow"].outputs[0], n["sub"].inputs[0])
    n["sub"].inputs[1].default_value = 1.0

    n["sqrt"] = ng.nodes.new("ShaderNodeMath")
    n["sqrt"].operation = "SQRT"
    L(ng, n["sub"].outputs[0], n["sqrt"].inputs[0])

    n["neg"] = ng.nodes.new("ShaderNodeMath")
    n["neg"].operation = "MULTIPLY"
    L(ng, n["sqrt"].outputs[0], n["neg"].inputs[0])
    n["neg"].inputs[1].default_value = -1.0

    n["cz"] = ng.nodes.new("ShaderNodeCombineXYZ")
    L(ng, n["neg"].outputs[0], n["cz"].inputs["Z"])

    n["tf"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["uv"].outputs["Mesh"], n["tf"].inputs["Geometry"])
    L(ng, n["cz"].outputs[0], n["tf"].inputs["Translation"])

    n["pos"] = ng.nodes.new("GeometryNodeInputPosition")
    n["sep"] = ng.nodes.new("ShaderNodeSeparateXYZ")
    L(ng, n["pos"].outputs[0], n["sep"].inputs[0])

    n["lt"] = ng.nodes.new("FunctionNodeCompare")
    n["lt"].operation = "LESS_THAN"
    L(ng, n["sep"].outputs["Z"], n["lt"].inputs[0])

    n["del"] = ng.nodes.new("GeometryNodeDeleteGeometry")
    L(ng, n["tf"].outputs[0], n["del"].inputs["Geometry"])
    L(ng, n["lt"].outputs[0], n["del"].inputs["Selection"])

    L(ng, n["del"].outputs[0], n["out"].inputs["Mesh"])

    return ng

def build_generate_table_top():
    ng = bpy.data.node_groups.new("generate_table_top", "GeometryNodeTree")
    ng.interface.new_socket("Thickness", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("N-gon", in_out="INPUT", socket_type="NodeSocketInt")
    ng.interface.new_socket("Profile Width", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Aspect Ratio", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Fillet Ratio", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Fillet Radius Vertical", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Curve", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    for item in ng.interface.items_tree:
        if hasattr(item, "default_value"):
            if item.name == "Thickness":
                item.default_value = 0.5
            elif item.name == "Profile Width":
                item.default_value = 0.5
            elif item.name == "Aspect Ratio":
                item.default_value = 0.5
            elif item.name == "Fillet Ratio":
                item.default_value = 0.2

    n = {}
    L = new_link

    n["in"] = ng.nodes.new("NodeGroupInput")
    n["out"] = ng.nodes.new("NodeGroupOutput")

    n["cl"] = ng.nodes.new("GeometryNodeCurvePrimitiveLine")
    n["cl"].inputs["Start"].default_value = (1.0, 0.0, 1.0)
    n["cl"].inputs["End"].default_value = (1.0, 0.0, -1.0)

    n["ngc"] = ng.nodes.new("GeometryNodeGroup")
    n["ngc"].node_tree = bpy.data.node_groups["n_gon_cylinder"]
    L(ng, n["cl"].outputs[0], n["ngc"].inputs["Radius Curve"])
    L(ng, n["in"].outputs["Thickness"], n["ngc"].inputs["Height"])
    L(ng, n["in"].outputs["N-gon"], n["ngc"].inputs["N-gon"])
    L(ng, n["in"].outputs["Profile Width"], n["ngc"].inputs["Profile Width"])
    L(ng, n["in"].outputs["Aspect Ratio"], n["ngc"].inputs["Aspect Ratio"])
    L(ng, n["in"].outputs["Fillet Ratio"], n["ngc"].inputs["Fillet Ratio"])
    n["ngc"].inputs["Profile Resolution"].default_value = 512
    n["ngc"].inputs["Resolution"].default_value = 10

    n["arc"] = ng.nodes.new("GeometryNodeCurveArc")
    n["arc"].inputs["Resolution"].default_value = 4
    n["arc"].inputs["Radius"].default_value = 0.7071
    n["arc"].inputs["Sweep Angle"].default_value = 4.7124

    n["t1"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["arc"].outputs["Curve"], n["t1"].inputs["Geometry"])
    n["t1"].inputs["Rotation"].default_value = (0, 0, -0.7854)

    n["t2"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["t1"].outputs[0], n["t2"].inputs["Geometry"])
    n["t2"].inputs["Rotation"].default_value = (0, math.pi / 2, 0)

    n["t3"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["t2"].outputs[0], n["t3"].inputs["Geometry"])
    n["t3"].inputs["Translation"].default_value = (0, 0.5, 0)

    n["cxyz_fr"] = ng.nodes.new("ShaderNodeCombineXYZ")
    n["cxyz_fr"].inputs["X"].default_value = 1.0
    L(ng, n["in"].outputs["Fillet Radius Vertical"], n["cxyz_fr"].inputs["Y"])
    n["cxyz_fr"].inputs["Z"].default_value = 1.0

    n["t4"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["t3"].outputs[0], n["t4"].inputs["Geometry"])
    L(ng, n["cxyz_fr"].outputs[0], n["t4"].inputs["Scale"])

    n["fc"] = ng.nodes.new("GeometryNodeFilletCurve")
    set_fillet_mode(n["fc"], "POLY")
    L(ng, n["t4"].outputs[0], n["fc"].inputs["Curve"])
    n["fc"].inputs["Count"].default_value = 8
    L(ng, n["in"].outputs["Fillet Radius Vertical"], n["fc"].inputs["Radius"])
    n["fc"].inputs["Limit Radius"].default_value = True

    n["t5"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["fc"].outputs[0], n["t5"].inputs["Geometry"])
    n["t5"].inputs["Rotation"].default_value = (math.pi / 2, math.pi / 2, 0)
    L(ng, n["in"].outputs["Thickness"], n["t5"].inputs["Scale"])

    n["c2m"] = ng.nodes.new("GeometryNodeCurveToMesh")
    L(ng, n["ngc"].outputs["Profile Curve"], n["c2m"].inputs["Curve"])
    L(ng, n["t5"].outputs[0], n["c2m"].inputs["Profile Curve"])

    n["mul_th"] = ng.nodes.new("ShaderNodeMath")
    n["mul_th"].operation = "MULTIPLY"
    L(ng, n["in"].outputs["Thickness"], n["mul_th"].inputs[0])
    n["mul_th"].inputs[1].default_value = -0.5

    n["cz_th"] = ng.nodes.new("ShaderNodeCombineXYZ")
    L(ng, n["mul_th"].outputs[0], n["cz_th"].inputs["Z"])

    n["t6"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["c2m"].outputs[0], n["t6"].inputs["Geometry"])
    L(ng, n["cz_th"].outputs[0], n["t6"].inputs["Translation"])

    n["idx"] = ng.nodes.new("GeometryNodeInputIndex")
    n["eq"] = ng.nodes.new("FunctionNodeCompare")
    n["eq"].data_type = "INT"
    n["eq"].operation = "EQUAL"
    L(ng, n["idx"].outputs[0], n["eq"].inputs[2])
    n["eq"].inputs[3].default_value = 0

    n["join"] = ng.nodes.new("GeometryNodeJoinGeometry")
    L(ng, n["t6"].outputs[0], n["join"].inputs["Geometry"])
    L(ng, n["ngc"].outputs["Caps"], n["join"].inputs["Geometry"])

    n["flip"] = ng.nodes.new("GeometryNodeFlipFaces")
    L(ng, n["join"].outputs[0], n["flip"].inputs["Mesh"])

    n["cz_up"] = ng.nodes.new("ShaderNodeCombineXYZ")
    L(ng, n["in"].outputs["Thickness"], n["cz_up"].inputs["Z"])

    n["t7"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["flip"].outputs[0], n["t7"].inputs["Geometry"])
    L(ng, n["cz_up"].outputs[0], n["t7"].inputs["Translation"])

    L(ng, n["t7"].outputs[0], n["out"].inputs["Geometry"])
    L(ng, n["ngc"].outputs["Profile Curve"], n["out"].inputs["Curve"])

    return ng

def sample_parameters():
    return {
        "Profile N-gon": 4,
        "Profile Width": 1.0,
        "Profile Aspect Ratio": 1.0,
        "Profile Fillet Ratio": 0.2,
        "Thickness": 0.1,
        "Vertical Fillet Ratio": 0.2,
    }

def create_table_top(params, mat_top=None):
    build_n_gon_profile()
    build_n_gon_cylinder()
    build_create_cap()
    build_generate_table_top()

    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = "TableTopFactory"

    ng = bpy.data.node_groups.new("table_top_wrapper", "GeometryNodeTree")
    geo_in = ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    n_in = ng.nodes.new("NodeGroupInput")
    n_out = ng.nodes.new("NodeGroupOutput")

    n_gtt = ng.nodes.new("GeometryNodeGroup")
    n_gtt.node_tree = bpy.data.node_groups["generate_table_top"]
    n_gtt.inputs["Thickness"].default_value = params["Thickness"]
    n_gtt.inputs["N-gon"].default_value = params["Profile N-gon"]
    n_gtt.inputs["Profile Width"].default_value = params["Profile Width"]
    n_gtt.inputs["Aspect Ratio"].default_value = params["Profile Aspect Ratio"]
    n_gtt.inputs["Fillet Ratio"].default_value = params["Profile Fillet Ratio"]
    n_gtt.inputs["Fillet Radius Vertical"].default_value = params["Vertical Fillet Ratio"]

    ng.links.new(n_gtt.outputs["Geometry"], n_out.inputs["Geometry"])

    mod = obj.modifiers.new("GeometryNodes", "NODES")
    mod.node_group = ng

    select_only(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # Clear any default material slots from the primitive, then assign
    obj.data.materials.clear()
    if mat_top is not None:
        obj.data.materials.append(mat_top)

    return obj

# Main — build with material
def build(seed=SEED):
    params = sample_parameters()
    obj = create_table_top(params, mat_top=MAT_TOP)
    if obj is not None:
        obj.name = "TableTopFactory"
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.shade_smooth()
        obj.select_set(False)
        obj.data.update()
    return obj

build(SEED)

