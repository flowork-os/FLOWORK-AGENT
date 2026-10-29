# [FL_INDEX: keywords="blender_factory, procedural_3d, CabinetFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: CabinetFactory | Category: factories_tex
# Prompt: A 3D model of a tall rectangular storage cabinet rendered from a three-quarter perspective, featuring a dark-colored box-like body with internal compartments divided by horizontal and vertical shelves, creating a grid of open cubby spaces.

# CabinetFactory — textured conversion
#
# Geometry copied verbatim from:
#   objects_blender/shelves/CabinetFactory.py
# Shaders translated faithfully from:
#                                                 shader_shelves_black_wood,
#                                                 shader_shelves_wood,
#                                                 get_shelf_material)
#
# Cabinet material binding model:
#   CabinetBaseFactory.get_material_params which samples a single `frame_material`
#   under FixedSeed(factory_seed) from {white, black_wood, wood} with
#   probabilities [0.5, 0.2, 0.3] and wraps it via plywood.get_shelf_material,
#   which in turn picks a shelves-specific shader OR the generic wood/plastic
#   counterpart. The single joined mesh receives this frame_material; the
#   source does not apply wear_tear inside the factory, but we include the
#   50/50 wear_tear gates here for parity with the texture-pipeline spec.

import os
import bpy
import bmesh
import math
import random
import colorsys
import hashlib
import numpy as np
from numpy.random import normal, randint, uniform

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

def _srgb_to_linear(c):
    if c < 0: return 0.0
    elif c < 0.04045: return c / 12.92
    else: return ((c + 0.055) / 1.055) ** 2.4

def _hex2rgba(hexval):
    r = ((hexval >> 16) & 0xFF) / 255.0
    g = ((hexval >> 8) & 0xFF) / 255.0
    b = (hexval & 0xFF) / 255.0
    return (_srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b), 1.0)

def _rgb2hsv(rgb):
    return colorsys.rgb_to_hsv(float(rgb[0]), float(rgb[1]), float(rgb[2]))

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

NATURAL_BASE_COLORS = [
    (0xC0C0C0, 1), (0x8C7853, 1), (0xBDBAAE, 1), (0xA9ACB6, 1), (0xB6AFA9, 1),
]

def _metal_natural_hsv():
    weights = np.array([w for _, w in NATURAL_BASE_COLORS], dtype=float)
    idx = int(np.random.choice(len(NATURAL_BASE_COLORS), p=weights / weights.sum()))
    hexval = NATURAL_BASE_COLORS[idx][0]
    h, s, v = _rgb2hsv(_hex2rgba(hexval)[:3])
    return (h + np.random.uniform(-0.1, 0.1),
            s + np.random.uniform(-0.1, 0.1),
            v * _mat_log_uniform(0.5, 0.2))

def metal_hsv():
    """py:metal_hsv with hex-based natural metals."""

    if np.random.uniform() < 0.2:
        return _metal_natural_hsv()
    return (np.random.uniform(0, 1),
            np.random.uniform(0.3, 0.6),
            _mat_log_uniform(0.02, 0.5))

def bark_hsv():
    """py:bark_hsv with sRGB-to-linear + full palette."""

    hexval = WOOD_COLORS[np.random.randint(0, len(WOOD_COLORS))]
    return _rgb2hsv(_hex2rgba(hexval)[:3])

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
    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Specular":           ("Specular IOR Level", "Specular"),
        "Coat Weight":        ("Coat Weight", "Clearcoat"),
        "Sheen Weight":       ("Sheen Weight", "Sheen"),
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
# Shelves-specific shaders (plywood.py)
# ----------------------------------------------------------------------------
def _shelves_wood_body(nt, wave_scale, z_axis_texture):
    """Shared node tree for shader_shelves_wood / shader_shelves_black_wood.

    Produces four outputs consumed by the caller:
      - base_color_fac (Fac socket feeding the Base Color ColorRamp)
      - disp_fac (mix_3 RGBA result used as displacement height source)
      - noise_distortion
      - wave_scale_tuple (for debugging)
    Matches plywood.py:shader_shelves_wood up to the Base Color colorramp.
    """

    tex_coord_1 = nt.nodes.new("ShaderNodeTexCoord")
    if z_axis_texture:
        wave_vec = (wave_scale, wave_scale, 0.1)
        map1_scale = (0.1, 0.1, 2.0)
    else:
        wave_vec = (wave_scale, 0.1, 0.1)
        map1_scale = (0.1, 2.0, 2.0)

    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    mapping_1.inputs["Scale"].default_value = map1_scale
    nt.links.new(tex_coord_1.outputs["Object"], mapping_1.inputs["Vector"])

    noise_1 = nt.nodes.new("ShaderNodeTexNoise")
    noise_1.inputs["Scale"].default_value = 100.0
    if "Detail" in noise_1.inputs:     noise_1.inputs["Detail"].default_value = 10.0
    if "Distortion" in noise_1.inputs: noise_1.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping_1.outputs["Vector"], noise_1.inputs["Vector"])

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.inputs["Scale"].default_value = 40.0
    nt.links.new(_noise_fac_output(noise_1), voronoi.inputs["Vector"])

    colorramp_1 = nt.nodes.new("ShaderNodeValToRGB")
    cr1_in = colorramp_1.inputs.get("Fac") or colorramp_1.inputs[0]
    vor_col = voronoi.outputs.get("Color") or voronoi.outputs[0]
    nt.links.new(vor_col, cr1_in)
    colorramp_1.color_ramp.elements[0].position = 0.0864
    colorramp_1.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    colorramp_1.color_ramp.elements[1].position = 0.1091
    colorramp_1.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = wave_vec
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    # Musgrave substitute — stretched NoiseTexture (Musgrave removed in 5.0)
    musgrave = nt.nodes.new("ShaderNodeTexNoise")
    musgrave.inputs["Scale"].default_value = 20.0
    if "Detail" in musgrave.inputs: musgrave.inputs["Detail"].default_value = 3.0
    nt.links.new(_noise_fac_output(noise), musgrave.inputs["Vector"])

    mix_1 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_1, "data_type"): mix_1.data_type = "RGBA"
    nt.links.new(_noise_fac_output(musgrave), mix_1.inputs[6])
    noise_col = noise.outputs.get("Color") or noise.outputs[0]
    nt.links.new(noise_col, mix_1.inputs[7])

    colorramp_2 = nt.nodes.new("ShaderNodeValToRGB")
    cr2_in = colorramp_2.inputs.get("Fac") or colorramp_2.inputs[0]
    nt.links.new(mix_1.outputs[2], cr2_in)
    colorramp_2.color_ramp.elements[0].position = 0.0818
    colorramp_2.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    colorramp_2.color_ramp.elements[1].position = 0.85
    colorramp_2.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    mix_2 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_2, "data_type"): mix_2.data_type = "RGBA"
    mix_2.inputs[0].default_value = 0.6
    nt.links.new(colorramp_1.outputs["Color"], mix_2.inputs[6])
    nt.links.new(colorramp_2.outputs["Color"], mix_2.inputs[7])

    mix_3 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_3, "data_type"): mix_3.data_type = "RGBA"
    mix_3.inputs[0].default_value = 0.004
    nt.links.new(colorramp_1.outputs["Color"], mix_3.inputs[6])
    nt.links.new(colorramp_2.outputs["Color"], mix_3.inputs[7])

    return mix_2.outputs[2], mix_3.outputs[2]

def make_shelves_white(name="ShelvesWhite") -> bpy.types.Material:
    """Re-impl of plywood.py:shader_shelves_white (uses sampler)."""

    v = float(np.random.uniform(0.7, 1.0))
    rgb = (
        v * (1.0 + float(np.random.normal(0, 0.005))),
        v * (1.0 + float(np.random.normal(0, 0.005))),
        v * (1.0 + float(np.random.normal(0, 0.005))),
        1.0,
    )
    roughness = float(np.random.uniform(0.7, 1.0))

    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=roughness)
    bsdf.inputs["Base Color"].default_value = rgb
    _connect_output(nt, bsdf)
    return mat

def make_shelves_black_wood(name="ShelvesBlackWood",
                            z_axis_texture=False) -> bpy.types.Material:
    """Re-impl of plywood.py:shader_shelves_black_wood (uses sampler)."""

    wave_scale = float(np.random.uniform(1.0, 3.0))
    dark_scale = float(np.random.uniform(0.0, 0.01))
    gray_scale = float(np.random.uniform(0.01, 0.03))
    rgb = (float(np.random.uniform(0.015, 0.035)),
           float(np.random.uniform(0.0, 0.01)),
           float(np.random.uniform(0.0, 0.01)))
    roughness = float(np.random.uniform(0.75, 1.0))

    mat = _new_material(name)
    nt = mat.node_tree
    base_fac, disp_fac = _shelves_wood_body(nt, wave_scale, z_axis_texture)

    # Base color ColorRamp with 3 dark stops
    cr_base = nt.nodes.new("ShaderNodeValToRGB")
    cr_in = cr_base.inputs.get("Fac") or cr_base.inputs[0]
    nt.links.new(base_fac, cr_in)
    elements = cr_base.color_ramp.elements
    elements[0].position = 0.15
    elements[0].color = (dark_scale, dark_scale, dark_scale, 1.0)
    e_mid = elements.new(0.5)
    e_mid.color = (gray_scale, gray_scale, gray_scale, 1.0)
    elements[-1].position = 1.0
    elements[-1].color = (rgb[0], rgb[1], rgb[2], 1.0)

    # Displacement
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.01
    nt.links.new(disp_fac, disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=roughness)
    nt.links.new(cr_base.outputs["Color"], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_shelves_wood(name="ShelvesWood",
                      z_axis_texture=False) -> bpy.types.Material:
    """Re-impl of plywood.py:shader_shelves_wood (uses sampler)."""

    bright_hsv = (float(np.random.uniform(0.03, 0.09)),
                  float(np.random.uniform(0.5, 0.7)),
                  float(np.random.uniform(0.7, 1.0)))
    mid_hsv = (float(np.random.uniform(0.02, 0.06)),
               float(np.random.uniform(0.6, 1.0)),
               float(np.random.uniform(0.3, 0.6)))
    dark_hsv = (float(np.random.uniform(0.03, 0.05)),
                float(np.random.uniform(0.6, 1.0)),
                float(np.random.uniform(0.1, 0.3)))
    wave_scale = float(np.random.uniform(1.0, 3.0))
    roughness = float(np.random.uniform(0.75, 1.0))

    mat = _new_material(name)
    nt = mat.node_tree
    base_fac, disp_fac = _shelves_wood_body(nt, wave_scale, z_axis_texture)

    cr_base = nt.nodes.new("ShaderNodeValToRGB")
    cr_in = cr_base.inputs.get("Fac") or cr_base.inputs[0]
    nt.links.new(base_fac, cr_in)
    elements = cr_base.color_ramp.elements
    elements[0].position = 0.02
    elements[0].color = hsv2rgba(dark_hsv)
    e_mid = elements.new(0.11)
    e_mid.color = hsv2rgba(mid_hsv)
    elements[-1].position = 0.8
    elements[-1].color = hsv2rgba(bright_hsv)

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.01
    nt.links.new(disp_fac, disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=roughness)
    nt.links.new(cr_base.outputs["Color"], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# ----------------------------------------------------------------------------
# Wood (bark-color variant) and rough plastic
# ----------------------------------------------------------------------------
def make_wood(name="Wood", color=None) -> bpy.types.Material:
    """Simplified re-impl of materials/wood/wood.py:shader_wood.

    Musgrave (removed in 5.0) replaced by stretched NoiseTexture.
    """

    if color is None:
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

    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    nt.links.new(_noise_fac_output(grain), mix.inputs[0])
    nt.links.new(hsv_node.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = color

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
    _set_principled(bsdf,
                    **{"Coat Weight": float(np.clip(np.random.uniform(0, 1.4), 0, 1))})
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_plastic_rough(name="PlasticRough", base_color=None) -> bpy.types.Material:
    """Re-impl of materials/plastic/plastic_rough.py."""

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
# Metal family
# ----------------------------------------------------------------------------
def make_metal_basic(name="MetalBasic", color_hsv=None) -> bpy.types.Material:
    """Re-impl of metal_basic.py:shader_metal."""

    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(np.random.uniform(10, 25))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    fc = _build_float_curve(
        nt,
        _noise_fac_output(noise),
        [(0, float(np.random.uniform(0, 0.2))),
         (1, float(np.random.uniform(0.4, 0.7)))],
    )

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Metallic=1.0,
                    **{"Specular IOR Level": float(np.random.uniform(0.5, 1.0))})
    bsdf.inputs["Base Color"].default_value = hsv2rgba(color_hsv or metal_hsv())
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_brushed_metal(name="BrushedMetal", base_color_hsv=None) -> bpy.types.Material:
    """Re-impl of brushed_metal.py."""

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
    """Re-impl of galvanized_metal.py."""

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
    _set_principled(bsdf, Metallic=1.0,
                    **{"Specular IOR Level": 0.0,
                       "Base Color": hsv2rgba(base_color_hsv)})
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_grained_metal(name="GrainedMetal", base_color_hsv=None) -> bpy.types.Material:
    """Re-impl of grained_and_polished_metal.py."""

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
    _set_principled(bsdf, Metallic=1.0,
                    **{"Specular IOR Level": 0.0,
                       "Base Color": hsv2rgba(base_color_hsv)})
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_hammered_metal(name="HammeredMetal", base_color_hsv=None) -> bpy.types.Material:
    """Re-impl of hammered_metal.py."""

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
    _set_principled(bsdf, Metallic=1.0,
                    **{"Specular IOR Level": 0.0,
                       "Base Color": hsv2rgba(base_color_hsv),
                       "Roughness": 0.1})
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_glass(name="Glass") -> bpy.types.Material:
    """Re-impl of ceramic/glass.py:shader_glass (non-window variant)."""

    mat = _new_material(name)
    nt = mat.node_tree
    glass = nt.nodes.new("ShaderNodeBsdfPrincipled")
    if "Roughness" in glass.inputs:
        glass.inputs["Roughness"].default_value = 0.02
    if "IOR" in glass.inputs:
        glass.inputs["IOR"].default_value = 1.5
    if "Transmission Weight" in glass.inputs:
        glass.inputs["Transmission Weight"].default_value = 1.0
    elif "Transmission" in glass.inputs:
        glass.inputs["Transmission"].default_value = 1.0
        if "Transmission Weight" in glass.inputs:
            glass.inputs["Transmission Weight"].default_value = 1.0
        elif "Transmission" in glass.inputs:
            glass.inputs["Transmission"].default_value = 1.0
    # plywood.get_shelf_material -> shader_glass -> get_glass_color(clear=False)
    if np.random.uniform() < 0.5:
        color = (1.0, 1.0, 1.0, 1.0)
    else:
        color = hsv2rgba((float(np.random.uniform(0, 1)),
                          float(np.random.uniform(0.05, 0.25)),
                          1.0))
    if "Color" in glass.inputs:
        glass.inputs["Base Color"].default_value = color
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(glass.outputs[0], out.inputs["Surface"])
    return mat

# ----------------------------------------------------------------------------
# Registries — mirror plywood.get_shelf_material dispatch for the three
# frame_material choices used by CabinetBaseFactory. Inner np.random.choice()
# selects the exact shader per bucket. Order/consumption mimics the source.
# ----------------------------------------------------------------------------
def get_shelf_material(name: str, slot_name: str = None) -> bpy.types.Material:
    """Re-impl of plywood.get_shelf_material(name). Consumes one np.random.choice
    for white/black_wood/wood buckets (matching weighted shader dispatch)."""

    slot_name = slot_name or name.title()
    if name == "white":
        ctor = [make_shelves_white, make_plastic_rough][
            int(np.random.choice(2, p=[0.6, 0.4]))]
        return ctor(name=slot_name)
    elif name == "black_wood":
        if int(np.random.choice(2, p=[0.6, 0.4])) == 0:
            return make_shelves_black_wood(name=slot_name)
        return make_wood(name=slot_name)
    elif name == "wood":
        if int(np.random.choice(2, p=[0.6, 0.4])) == 0:
            return make_shelves_wood(name=slot_name)
        return make_wood(name=slot_name)
    elif name == "glass":
        return make_glass(name=slot_name)
    elif name == "metal":
        metal_ctors = [make_brushed_metal, make_galvanized_metal,
                       make_grained_metal, make_hammered_metal, make_metal_basic]
        ctor = metal_ctors[int(np.random.choice(5))]
        return ctor(name=slot_name)
    else:
        ctors = [make_shelves_white, make_plastic_rough,
                 make_shelves_black_wood, make_wood, make_shelves_wood]
        ctor = ctors[int(np.random.choice(5, p=[0.3, 0.2, 0.3, 0.1, 0.1]))]
        return ctor(name=slot_name)

# wear_tear post-processing (mirrors BedFrameFactory port)
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

# Scene cleanup
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
for ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(ng)
bpy.context.scene.cursor.location = (0, 0, 0)

# FixedSeed(factory_seed)). Material sampling order follows cabinet.py:
#   CabinetBaseFactory.get_material_params()
#     1. frame_material = np.random.choice(["white","black_wood","wood"],
#                                          p=[0.5, 0.2, 0.3])
#     2. get_shelf_material(frame_material)  — consumes one inner np.random.choice
# then wear_tear probability gates (50/50 each) kept for texture-pipeline parity.
SEED = int(os.environ.get('SEED', 0))
seed_all(SEED)

_FRAME_NAME = ["white", "black_wood", "wood"][
    int(np.random.choice(3, p=[0.5, 0.2, 0.3]))]
MAT_FRAME = get_shelf_material(_FRAME_NAME, slot_name="CabinetFrame")

# Metal material for cabinet hardware (attach/hinge/handle), matching
# cabinet.py lines 1259 and 1381 where `get_shelf_material("metal")`
# is used inside the geometry_cabinet_nodes SetMaterial pipeline for attach parts.
_saved_state = np.random.get_state()
MAT_METAL = get_shelf_material("metal", slot_name="CabinetMetal")
np.random.set_state(_saved_state)

_scratch_p, _edge_wear_p = WEAR_TEAR_PROB
WEAR_DO_SCRATCH  = (np.random.uniform() <= _scratch_p)
WEAR_DO_EDGEWEAR = (np.random.uniform() <= _edge_wear_p)

# --- Original geometry code (copied verbatim from
#     objects_blender/shelves/CabinetFactory.py) =============================

def apply_transform(obj, loc=False, rot=True, scale=True):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=loc, rotation=rot, scale=scale)
    obj.select_set(False)
    return obj

# --- Node system ---

def to_nodegroup(name):
    def reg(fn):
        def init_fn(*args, **kw):
            ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
            fn(NodeWrangler(ng), *args, **kw)
            return ng
        return init_fn
    return reg

def _infer_output_socket(item):
    if isinstance(item, bpy.types.NodeSocket): return item
    if outputs := getattr(item, 'outputs', None):
        return next((s for s in outputs if getattr(s, 'enabled', True)), outputs[0])

class NodeWrangler:
    def __init__(self, node_group_or_mod):
        ng = self.node_group = node_group_or_mod.node_group if isinstance(node_group_or_mod, bpy.types.NodesModifier) else node_group_or_mod
        self.nodes, self.links = ng.nodes, ng.links

    def expose_input(self, name, val=None, dtype=None):
        gi = next((n for n in self.nodes if n.bl_idname == 'NodeGroupInput'), None) or self.nodes.new('NodeGroupInput')
        inames = [s.name for s in self.node_group.interface.items_tree if s.in_out == 'INPUT']
        if name not in inames:
            self.node_group.interface.new_socket(name=name, in_out='INPUT', socket_type=dtype or 'NodeSocketFloat')
            inames.append(name)
        try: return gi.outputs[name]
        except Exception: return gi.outputs[inames.index(name)]

    def connect_input(self, sock, item):
        for sub in (item if isinstance(item, list) else [item]):
            out = _infer_output_socket(sub)
            if out is not None:
                try: self.links.new(out, sock)
                except Exception: pass
            elif not isinstance(item, list):
                try: sock.default_value = sub
                except Exception:
                    try: sock.default_value = tuple(sub)
                    except Exception: pass

    def new_node(self, node_type, input_kwargs=None, attrs=None, expose_input=None):
        if expose_input:
            for dtype, name, val in expose_input:
                self.expose_input(name, val=val, dtype=dtype)
        ng_ref = bpy.data.node_groups.get(node_type)
        if ng_ref is not None:
            n = self.nodes.new('GeometryNodeGroup'); n.node_tree = ng_ref
        else:
            n = self.nodes.new(node_type)
        if attrs:
            for k, v in attrs.items():
                try: setattr(n, k, v)
                except Exception: pass
        if input_kwargs:
            is_go = (n.bl_idname == 'NodeGroupOutput')
            for k, item in input_kwargs.items():
                if is_go and isinstance(k, str) and k not in [s.name for s in n.inputs]:
                    out_sock = _infer_output_socket(item)
                    st = getattr(out_sock, 'bl_idname', 'NodeSocketFloat') if out_sock else 'NodeSocketFloat'
                    st = {'NodeSocketFloatUnsigned': 'NodeSocketFloat', 'NodeSocketVirtual': 'NodeSocketFloat'}.get(st, st)
                    try: self.node_group.interface.new_socket(name=k, in_out='OUTPUT', socket_type=st)
                    except Exception: pass
                try: self.connect_input(n.inputs[k], item)
                except Exception:
                    try:
                        self.connect_input(n.inputs[[s.name for s in n.inputs].index(k)], item)
                    except Exception: pass
        return n

    def val(self, v):
        n = self.new_node('ShaderNodeValue'); n.outputs[0].default_value = v; return n

def make_geo_object(geo_func, kwargs):
    bpy.ops.mesh.primitive_plane_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    ng = bpy.data.node_groups.new('Geometry Nodes', 'GeometryNodeTree')
    ng.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    mod = obj.modifiers.new(geo_func.__name__, 'NODES')
    mod.node_group = ng
    geo_func(NodeWrangler(mod), **kwargs)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.select_set(False)
    return obj

# --- Node type constants ---

class Nodes:
    BooleanMath = 'FunctionNodeBooleanMath'
    CombineXYZ = 'ShaderNodeCombineXYZ'
    ConvexHull = 'GeometryNodeConvexHull'
    CurveCircle = 'GeometryNodeCurvePrimitiveCircle'
    CurveLine = 'GeometryNodeCurvePrimitiveLine'
    CurveToMesh = 'GeometryNodeCurveToMesh'
    EndpointSelection = 'GeometryNodeCurveEndpointSelection'
    FlipFaces = 'GeometryNodeFlipFaces'
    GroupInput = 'NodeGroupInput'
    GroupOutput = 'NodeGroupOutput'
    Index = 'GeometryNodeInputIndex'
    JoinGeometry = 'GeometryNodeJoinGeometry'
    Math = 'ShaderNodeMath'
    MergeByDistance = 'GeometryNodeMergeByDistance'
    MeshCube = 'GeometryNodeMeshCube'
    RealizeInstances = 'GeometryNodeRealizeInstances'
    SetPosition = 'GeometryNodeSetPosition'
    Transform = 'GeometryNodeTransform'

# Shelf nodegroup functions

@to_nodegroup("nodegroup_screw_head")
def nodegroup_screw_head(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "Depth", 0.0050),
        ("NodeSocketFloat", "Radius", 1.0000),
        ("NodeSocketFloat", "division_thickness", 0.5000),
        ("NodeSocketFloat", "width", 0.5000),
        ("NodeSocketFloat", "depth", 0.5000),
        ("NodeSocketFloat", "screw_width_gap", 0.5000),
        ("NodeSocketFloat", "screw_depth_gap", 0.0000),
    ])

    cylinder = nw.new_node("GeometryNodeMeshCylinder",
        input_kwargs={"Radius": group_input.outputs["Radius"], "Depth": group_input.outputs["Depth"]},
        attrs={"fill_type": "TRIANGLE_FAN"})

    multiply = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["width"]}, attrs={"operation": "MULTIPLY"})
    subtract = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: group_input.outputs["screw_width_gap"]}, attrs={"operation": "SUBTRACT"})
    multiply_1 = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["depth"]}, attrs={"operation": "MULTIPLY"})
    subtract_1 = nw.new_node(Nodes.Math, input_kwargs={0: multiply_1, 1: group_input.outputs["screw_width_gap"]}, attrs={"operation": "SUBTRACT"})
    multiply_2 = nw.new_node(Nodes.Math, input_kwargs={0: subtract_1, 1: -1.0000}, attrs={"operation": "MULTIPLY"})
    multiply_3 = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["division_thickness"], 1: -0.5000}, attrs={"operation": "MULTIPLY"})

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": subtract, "Y": multiply_2, "Z": multiply_3})

    transform_1 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cylinder.outputs["Mesh"], "Translation": combine_xyz})

    combine_xyz_4 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": subtract, "Y": subtract_1, "Z": multiply_3})

    transform_6 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cylinder.outputs["Mesh"], "Translation": combine_xyz_4})

    join_geometry_2 = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [transform_1, transform_6]})

    transform_4 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": join_geometry_2, "Scale": (-1.0000, 1.0000, 1.0000)})

    join_geometry_3 = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [transform_4, join_geometry_2]})

    realize_instances = nw.new_node(Nodes.RealizeInstances, input_kwargs={"Geometry": join_geometry_3})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": realize_instances})

@to_nodegroup("nodegroup_division_board")
def nodegroup_division_board(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "thickness", 0.0000),
        ("NodeSocketFloat", "width", 0.0000),
        ("NodeSocketFloat", "depth", 0.0000),
        ("NodeSocketFloat", "z_translation", 0.0000),
        ("NodeSocketFloat", "x_translation", 0.0000),
        ("NodeSocketFloat", "screw_depth", 0.0000),
        ("NodeSocketFloat", "screw_radius", 0.0000),
        ("NodeSocketFloat", "screw_width_gap", 0.0000),
        ("NodeSocketFloat", "screw_depth_gap", 0.0000),
    ])

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={
        "X": group_input.outputs["width"], "Y": group_input.outputs["depth"], "Z": group_input.outputs["thickness"]})
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz})

    screw_head = nw.new_node(nodegroup_screw_head().name, input_kwargs={
        "Depth": group_input.outputs["screw_depth"], "Radius": group_input.outputs["screw_radius"],
        "division_thickness": group_input.outputs["thickness"], "width": group_input.outputs["width"],
        "depth": group_input.outputs["depth"], "screw_width_gap": group_input.outputs["screw_width_gap"],
        "screw_depth_gap": group_input.outputs["screw_depth_gap"]})

    join_geometry = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [cube, screw_head]})
    combine_xyz_1 = nw.new_node(Nodes.CombineXYZ, input_kwargs={
        "X": group_input.outputs["x_translation"], "Z": group_input.outputs["z_translation"]})

    transform = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": join_geometry, "Translation": combine_xyz_1})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": transform})

@to_nodegroup("nodegroup_bottom_board")
def nodegroup_bottom_board(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "thickness", 0.0000),
        ("NodeSocketFloat", "depth", 0.5000),
        ("NodeSocketFloat", "y_gap", 0.5000),
        ("NodeSocketFloat", "x_translation", 0.0000),
        ("NodeSocketFloat", "height", 0.5000),
        ("NodeSocketFloat", "width", 0.0000),
    ])

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={
        "X": group_input.outputs["width"], "Y": group_input.outputs["thickness"], "Z": group_input.outputs["height"]})
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz})

    multiply = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["depth"]}, attrs={"operation": "MULTIPLY"})
    subtract = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: group_input.outputs["y_gap"]}, attrs={"operation": "SUBTRACT"})
    multiply_1 = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["height"]}, attrs={"operation": "MULTIPLY"})
    combine_xyz_1 = nw.new_node(Nodes.CombineXYZ, input_kwargs={
        "X": group_input.outputs["x_translation"], "Y": subtract, "Z": multiply_1})

    transform = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_1})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": transform})

@to_nodegroup("nodegroup_back_board")
def nodegroup_back_board(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "width", 0.0000),
        ("NodeSocketFloat", "thickness", 0.5000),
        ("NodeSocketFloat", "height", 0.5000),
        ("NodeSocketFloat", "depth", 0.5000),
    ])

    combine_xyz_4 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": group_input.outputs["width"], "Y": group_input.outputs["thickness"], "Z": group_input.outputs["height"]})

    cube_2 = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz_4})

    multiply = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["thickness"], 1: -0.5000}, attrs={"operation": "MULTIPLY"})
    multiply_add = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["depth"], 1: -0.5000, 2: multiply}, attrs={"operation": "MULTIPLY_ADD"})
    multiply_1 = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["height"]}, attrs={"operation": "MULTIPLY"})

    combine_xyz_5 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": multiply_add, "Z": multiply_1})

    transform_5 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube_2, "Translation": combine_xyz_5})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": transform_5})

@to_nodegroup("nodegroup_side_board")
def nodegroup_side_board(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "board_thickness", 0.5000),
        ("NodeSocketFloat", "depth", 0.5000),
        ("NodeSocketFloat", "height", 0.5000),
        ("NodeSocketFloat", "x_translation", 0.0000),
    ])

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": group_input.outputs["board_thickness"], "Y": group_input.outputs["depth"], "Z": group_input.outputs["height"]})

    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz})

    multiply = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["height"], 1: 0.5000}, attrs={"operation": "MULTIPLY"})
    combine_xyz_1 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": group_input.outputs["x_translation"], "Z": multiply})

    transform = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_1})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": transform})

def geometry_nodes(nw: NodeWrangler, **kwargs):
    side_board_thickness = nw.val(kwargs["side_board_thickness"])
    shelf_depth = nw.val(kwargs["shelf_depth"])

    add = nw.new_node(Nodes.Math, input_kwargs={0: shelf_depth, 1: 0.0040})

    shelf_height = nw.val(kwargs["shelf_height"])

    add_1 = nw.new_node(Nodes.Math, input_kwargs={0: shelf_height, 1: 0.0020})
    add_2 = nw.new_node(Nodes.Math, input_kwargs={0: shelf_height, 1: -0.0010})
    _sb = nodegroup_side_board().name
    side_boards = [
        nw.new_node(_sb, input_kwargs={"board_thickness": side_board_thickness, "depth": add, "height": add_1, "x_translation": nw.val(x)})
        for x in kwargs["side_board_x_translation"]
    ]

    shelf_width = nw.val(kwargs["shelf_width"])
    backboard_thickness = nw.val(kwargs["backboard_thickness"])
    add_side = nw.new_node(Nodes.Math, input_kwargs={0: shelf_width, 1: kwargs["side_board_thickness"] * 2})
    back_board = nw.new_node(nodegroup_back_board().name, input_kwargs={
        "width": add_side, "thickness": backboard_thickness, "height": add_2, "depth": shelf_depth})

    bottom_board_y_gap = nw.val(kwargs["bottom_board_y_gap"])
    bottom_board_height = nw.val(kwargs["bottom_board_height"])
    _bb = nodegroup_bottom_board().name
    bottom_boards = [
        nw.new_node(_bb, input_kwargs={"thickness": side_board_thickness, "depth": shelf_depth,
            "y_gap": bottom_board_y_gap, "x_translation": nw.val(kwargs["bottom_gap_x_translation"][i]),
            "height": bottom_board_height, "width": nw.val(kwargs["shelf_cell_width"][i])})
        for i in range(len(kwargs["shelf_cell_width"]))
    ]

    join_geometry = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [back_board] + side_boards + bottom_boards})
    realize_instances = nw.new_node(Nodes.RealizeInstances, input_kwargs={"Geometry": join_geometry})

    division_board_thickness = nw.val(kwargs["division_board_thickness"])
    screw_depth_head = nw.val(kwargs["screw_depth_head"])
    screw_head_radius = nw.val(kwargs["screw_head_radius"])
    screw_width_gap = nw.val(kwargs["screw_width_gap"])
    screw_depth_gap = nw.val(kwargs["screw_depth_gap"])
    _db = nodegroup_division_board().name
    division_boards = [
        nw.new_node(_db, input_kwargs={"thickness": division_board_thickness,
            "width": nw.val(kwargs["shelf_cell_width"][i]), "depth": shelf_depth,
            "z_translation": nw.val(kwargs["division_board_z_translation"][j]),
            "x_translation": nw.val(kwargs["division_board_x_translation"][i]),
            "screw_depth": screw_depth_head, "screw_radius": screw_head_radius,
            "screw_width_gap": screw_width_gap, "screw_depth_gap": screw_depth_gap})
        for i in range(len(kwargs["shelf_cell_width"]))
        for j in range(len(kwargs["division_board_z_translation"]))
    ]

    join_geometry_k = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": division_boards})

    join_geometry_3 = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [realize_instances, join_geometry_k]})

    realize_instances_3 = nw.new_node(Nodes.RealizeInstances, input_kwargs={"Geometry": join_geometry_3})

    triangulate = nw.new_node("GeometryNodeTriangulate", input_kwargs={"Mesh": realize_instances_3})

    transform = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": triangulate, "Rotation": (0.0000, 0.0000, -1.5708)})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": transform})

# Door nodegroup functions

@to_nodegroup("nodegroup_node_group")
def nodegroup_node_group(nw: NodeWrangler):
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": (0.0120, 0.00060, 0.0400)})

    cylinder = nw.new_node("GeometryNodeMeshCylinder", input_kwargs={"Vertices": 16, "Radius": 0.0100, "Depth": 0.00050})
    transform = nw.new_node(Nodes.Transform, input_kwargs={
        "Geometry": cylinder.outputs["Mesh"], "Translation": (0.0050, 0.0000, 0.0000), "Rotation": (1.5708, 0.0000, 0.0000)})

    cube_1 = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": (0.0200, 0.0006, 0.0120)})

    transform_1 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube_1, "Translation": (0.0080, 0.0000, 0.0000)})

    join_geometry_1 = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [cube, transform, transform_1]})

    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "attach_height", 0.1000),
        ("NodeSocketFloat", "door_width", 0.5000),
    ])

    multiply = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["door_width"]}, attrs={"operation": "MULTIPLY"})

    subtract = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: 0.0181}, attrs={"operation": "SUBTRACT"})

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": subtract, "Z": group_input.outputs["attach_height"]})

    transform_2 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": join_geometry_1, "Translation": combine_xyz})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": transform_2})

@to_nodegroup("nodegroup_knob_handle")
def nodegroup_knob_handle(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "Radius", 0.0100),
        ("NodeSocketFloat", "thickness_1", 0.5000),
        ("NodeSocketFloat", "thickness_2", 0.5000),
        ("NodeSocketFloat", "length", 0.5000),
        ("NodeSocketFloat", "knob_mid_height", 0.0000),
        ("NodeSocketFloat", "edge_width", 0.5000),
        ("NodeSocketFloat", "door_width", 0.5000),
    ])

    add = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["thickness_2"], 1: group_input.outputs["thickness_1"]})
    add_1 = nw.new_node(Nodes.Math, input_kwargs={0: add, 1: group_input.outputs["length"]})
    cylinder = nw.new_node("GeometryNodeMeshCylinder",
        input_kwargs={"Vertices": 16, "Radius": group_input.outputs["Radius"], "Depth": add_1})
    subtract = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["door_width"], 1: group_input.outputs["edge_width"]}, attrs={"operation": "SUBTRACT"})
    multiply = nw.new_node(Nodes.Math, input_kwargs={0: subtract, 1: -0.5000}, attrs={"operation": "MULTIPLY"})
    add_2 = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: -0.005})
    multiply_1 = nw.new_node(Nodes.Math, input_kwargs={0: add_1}, attrs={"operation": "MULTIPLY"})

    combine_xyz_6 = nw.new_node(Nodes.CombineXYZ, input_kwargs={
        "X": add_2, "Y": multiply_1, "Z": group_input.outputs["knob_mid_height"]})

    transform_6 = nw.new_node(Nodes.Transform, input_kwargs={
        "Geometry": cylinder.outputs["Mesh"], "Translation": combine_xyz_6, "Rotation": (1.5708, 0.0000, 0.0000)})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": transform_6})

@to_nodegroup("nodegroup_mid_board")
def nodegroup_mid_board(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "height", 0.5000),
        ("NodeSocketFloat", "thickness", 0.5000),
        ("NodeSocketFloat", "width", 0.5000),
    ])

    add = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["width"], 1: -0.0001})
    multiply = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["height"]}, attrs={"operation": "MULTIPLY"})

    multiply_k = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["thickness"], 1: 0.5000}, attrs={"operation": "MULTIPLY"})
    add_k = nw.new_node(Nodes.Math, input_kwargs={0: multiply_k, 1: 0.004})
    add_2 = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: -0.0001})
    combine_xyz_3 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": add, "Y": group_input.outputs["thickness"], "Z": add_2})
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz_3})
    multiply_1 = nw.new_node(Nodes.Math, input_kwargs={0: multiply}, attrs={"operation": "MULTIPLY"})
    combine_xyz_4 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": add_k, "Z": multiply_1})
    transform_4 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_4})
    cube_1 = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz_3})
    multiply_2 = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: 1.5000}, attrs={"operation": "MULTIPLY"})

    combine_xyz_8 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": add_k, "Z": multiply_2})

    transform_7 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube_1, "Translation": combine_xyz_8})

    join_geometry_1 = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [transform_4, transform_7]})

    realize_instances = nw.new_node(Nodes.RealizeInstances, input_kwargs={"Geometry": join_geometry_1})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": realize_instances, "mid_height": multiply})

@to_nodegroup("nodegroup_mid_board_001")
def nodegroup_mid_board_001(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "height", 0.5000),
        ("NodeSocketFloat", "thickness", 0.5000),
        ("NodeSocketFloat", "width", 0.5000),
    ])

    add = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["width"], 1: -0.0001})
    multiply_k = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["thickness"], 1: 0.5000}, attrs={"operation": "MULTIPLY"})
    add_k = nw.new_node(Nodes.Math, input_kwargs={0: multiply_k, 1: 0.004})
    add_2 = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["height"], 1: -0.0001})
    combine_xyz_3 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": add, "Y": group_input.outputs["thickness"], "Z": add_2})
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz_3})
    multiply_1 = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["height"]}, attrs={"operation": "MULTIPLY"})

    combine_xyz_4 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": add_k, "Z": multiply_1})

    transform_4 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_4})

    realize_instances = nw.new_node(Nodes.RealizeInstances, input_kwargs={"Geometry": transform_4})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": realize_instances, "mid_height": group_input.outputs["height"]})

@to_nodegroup("nodegroup_double_rampled_edge")
def nodegroup_double_rampled_edge(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "height", 0.5000),
        ("NodeSocketFloat", "thickness_2", 0.5000),
        ("NodeSocketFloat", "width", 0.5000),
        ("NodeSocketFloat", "thickness_1", 0.5000),
        ("NodeSocketFloat", "ramp_angle", 0.5000),
    ])

    h = group_input.outputs["height"]
    w = group_input.outputs["width"]
    ra = group_input.outputs["ramp_angle"]
    t2 = group_input.outputs["thickness_2"]
    t1 = group_input.outputs["thickness_1"]

    combine_xyz_10 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": h})
    curve_line = nw.new_node(Nodes.CurveLine, input_kwargs={"End": combine_xyz_10})
    curve_circle = nw.new_node(Nodes.CurveCircle, input_kwargs={"Resolution": 2, "Radius": 0.0100})
    endpoint_selection = nw.new_node(Nodes.EndpointSelection, input_kwargs={"End Size": 0})

    tangent = nw.new_node(Nodes.Math, input_kwargs={0: ra}, attrs={"operation": "TANGENT"})
    multiply = nw.new_node(Nodes.Math, input_kwargs={0: tangent, 1: t2}, attrs={"operation": "MULTIPLY"})
    multiply_1 = nw.new_node(Nodes.Math, input_kwargs={0: 2.0000, 1: multiply}, attrs={"operation": "MULTIPLY"})
    subtract = nw.new_node(Nodes.Math, input_kwargs={0: w, 1: multiply_1}, attrs={"operation": "SUBTRACT"})
    multiply_2 = nw.new_node(Nodes.Math, input_kwargs={0: subtract}, attrs={"operation": "MULTIPLY"})
    multiply_3 = nw.new_node(Nodes.Math, input_kwargs={0: multiply_2, 1: -1.0000}, attrs={"operation": "MULTIPLY"})
    combine_xyz_7 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_3, "Y": t1})
    set_position = nw.new_node(Nodes.SetPosition,
        input_kwargs={"Geometry": curve_circle.outputs["Curve"], "Selection": endpoint_selection, "Position": combine_xyz_7})

    endpoint_selection_1 = nw.new_node(Nodes.EndpointSelection, input_kwargs={"Start Size": 0})
    add_5 = nw.new_node(Nodes.Math, input_kwargs={0: t1, 1: t2})
    combine_xyz_8 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_3, "Y": add_5})
    set_position_1 = nw.new_node(Nodes.SetPosition,
        input_kwargs={"Geometry": set_position, "Selection": endpoint_selection_1, "Position": combine_xyz_8})

    index = nw.new_node(Nodes.Index)
    less_than = nw.new_node(Nodes.Math, input_kwargs={0: index, 1: 1.0100}, attrs={"operation": "LESS_THAN"})
    greater_than = nw.new_node(Nodes.Math, input_kwargs={0: index, 1: 0.9900}, attrs={"operation": "GREATER_THAN"})
    op_and = nw.new_node(Nodes.BooleanMath, input_kwargs={0: less_than, 1: greater_than})
    multiply_4 = nw.new_node(Nodes.Math, input_kwargs={0: w}, attrs={"operation": "MULTIPLY"})
    multiply_5 = nw.new_node(Nodes.Math, input_kwargs={0: multiply_4, 1: -1.0000}, attrs={"operation": "MULTIPLY"})

    combine_xyz_9 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_5, "Y": t1})

    set_position_2 = nw.new_node(Nodes.SetPosition,
        input_kwargs={"Geometry": set_position_1, "Selection": op_and, "Position": combine_xyz_9})
    curve_to_mesh = nw.new_node(Nodes.CurveToMesh,
        input_kwargs={"Curve": curve_line, "Profile Curve": set_position_2, "Fill Caps": True})

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": w, "Y": t1, "Z": h})
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz})
    multiply_6 = nw.new_node(Nodes.Math, input_kwargs={0: t1}, attrs={"operation": "MULTIPLY"})
    combine_xyz_2 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": multiply_6})
    transform = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_2})

    combine_xyz_1 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": subtract, "Y": t2, "Z": h})
    cube_1 = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz_1})
    multiply_7 = nw.new_node(Nodes.Math, input_kwargs={0: t2}, attrs={"operation": "MULTIPLY"})
    add_6 = nw.new_node(Nodes.Math, input_kwargs={0: t1, 1: multiply_7})
    combine_xyz_3 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": add_6})
    transform_1 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube_1, "Translation": combine_xyz_3})
    join_geometry = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [transform, transform_1]})

    multiply_8 = nw.new_node(Nodes.Math, input_kwargs={0: h}, attrs={"operation": "MULTIPLY"})
    combine_xyz_11 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": multiply_8})
    transform_4 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": join_geometry, "Translation": combine_xyz_11})

    combine_xyz_12 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": h})
    curve_line_1 = nw.new_node(Nodes.CurveLine, input_kwargs={"End": combine_xyz_12})
    transform_2 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": set_position_2, "Scale": (-1.0000, 1.0000, 1.0000)})
    curve_to_mesh_1 = nw.new_node(Nodes.CurveToMesh,
        input_kwargs={"Curve": curve_line_1, "Profile Curve": transform_2, "Fill Caps": True})

    join_geometry_1 = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [curve_to_mesh, transform_4, curve_to_mesh_1]})

    merge_by_distance = nw.new_node(Nodes.MergeByDistance, input_kwargs={"Geometry": join_geometry_1, "Distance": 0.0001})

    realize_instances = nw.new_node(Nodes.RealizeInstances, input_kwargs={"Geometry": merge_by_distance})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": realize_instances})

@to_nodegroup("nodegroup_ramped_edge")
def nodegroup_ramped_edge(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "height", 0.5000),
        ("NodeSocketFloat", "thickness_2", 0.5000),
        ("NodeSocketFloat", "width", 0.5000),
        ("NodeSocketFloat", "thickness_1", 0.5000),
        ("NodeSocketFloat", "ramp_angle", 0.5000),
    ])

    h = group_input.outputs["height"]
    w = group_input.outputs["width"]
    ra = group_input.outputs["ramp_angle"]
    t2 = group_input.outputs["thickness_2"]
    t1 = group_input.outputs["thickness_1"]

    combine_xyz_10 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": h})
    curve_line = nw.new_node(Nodes.CurveLine, input_kwargs={"End": combine_xyz_10})
    curve_circle = nw.new_node(Nodes.CurveCircle, input_kwargs={"Resolution": 2, "Radius": 0.0100})
    endpoint_selection = nw.new_node(Nodes.EndpointSelection, input_kwargs={"End Size": 0})

    multiply = nw.new_node(Nodes.Math, input_kwargs={0: w}, attrs={"operation": "MULTIPLY"})
    tangent = nw.new_node(Nodes.Math, input_kwargs={0: ra}, attrs={"operation": "TANGENT"})
    multiply_1 = nw.new_node(Nodes.Math, input_kwargs={0: tangent, 1: t2}, attrs={"operation": "MULTIPLY"})
    subtract = nw.new_node(Nodes.Math, input_kwargs={0: w, 1: multiply_1}, attrs={"operation": "SUBTRACT"})
    subtract_1 = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: subtract}, attrs={"operation": "SUBTRACT"})
    combine_xyz_7 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": subtract_1, "Y": t1})
    set_position = nw.new_node(Nodes.SetPosition,
        input_kwargs={"Geometry": curve_circle.outputs["Curve"], "Selection": endpoint_selection, "Position": combine_xyz_7})

    endpoint_selection_1 = nw.new_node(Nodes.EndpointSelection, input_kwargs={"Start Size": 0})
    add_5 = nw.new_node(Nodes.Math, input_kwargs={0: t1, 1: t2})
    combine_xyz_8 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": subtract_1, "Y": add_5})
    set_position_1 = nw.new_node(Nodes.SetPosition,
        input_kwargs={"Geometry": set_position, "Selection": endpoint_selection_1, "Position": combine_xyz_8})

    index = nw.new_node(Nodes.Index)
    less_than = nw.new_node(Nodes.Math, input_kwargs={0: index, 1: 1.0100}, attrs={"operation": "LESS_THAN"})
    greater_than = nw.new_node(Nodes.Math, input_kwargs={0: index, 1: 0.9900}, attrs={"operation": "GREATER_THAN"})
    op_and = nw.new_node(Nodes.BooleanMath, input_kwargs={0: less_than, 1: greater_than})
    multiply_2 = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: -1.0000}, attrs={"operation": "MULTIPLY"})
    combine_xyz_9 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_2, "Y": t1})
    set_position_2 = nw.new_node(Nodes.SetPosition,
        input_kwargs={"Geometry": set_position_1, "Selection": op_and, "Position": combine_xyz_9})
    curve_to_mesh = nw.new_node(Nodes.CurveToMesh,
        input_kwargs={"Curve": curve_line, "Profile Curve": set_position_2, "Fill Caps": True})

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": w, "Y": t1, "Z": h})
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz})
    multiply_3 = nw.new_node(Nodes.Math, input_kwargs={0: t1}, attrs={"operation": "MULTIPLY"})
    combine_xyz_2 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": multiply_3})
    transform = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_2})

    combine_xyz_1 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": subtract, "Y": t2, "Z": h})
    cube_1 = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz_1})
    multiply_4 = nw.new_node(Nodes.Math, input_kwargs={0: multiply_1}, attrs={"operation": "MULTIPLY"})
    multiply_5 = nw.new_node(Nodes.Math, input_kwargs={0: t2}, attrs={"operation": "MULTIPLY"})
    add_6 = nw.new_node(Nodes.Math, input_kwargs={0: t1, 1: multiply_5})
    combine_xyz_3 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_4, "Y": add_6})
    transform_1 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube_1, "Translation": combine_xyz_3})
    join_geometry = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [transform, transform_1]})

    multiply_6 = nw.new_node(Nodes.Math, input_kwargs={0: h}, attrs={"operation": "MULTIPLY"})
    combine_xyz_11 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": multiply_6})
    transform_4 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": join_geometry, "Translation": combine_xyz_11})
    join_geometry_1 = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [curve_to_mesh, transform_4]})
    merge_by_distance = nw.new_node(Nodes.MergeByDistance, input_kwargs={"Geometry": join_geometry_1, "Distance": 0.0001})
    realize_instances = nw.new_node(Nodes.RealizeInstances, input_kwargs={"Geometry": merge_by_distance})

    multiply_7 = nw.new_node(Nodes.Math, input_kwargs={0: w, 1: -0.5000}, attrs={"operation": "MULTIPLY"})
    combine_xyz_4 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_7})

    transform_2 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": realize_instances, "Translation": combine_xyz_4})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": transform_2})

@to_nodegroup("nodegroup_panel_edge_frame")
def nodegroup_panel_edge_frame(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketGeometry", "vertical_edge", None),
        ("NodeSocketFloat", "door_width", 0.5000),
        ("NodeSocketFloat", "door_height", 0.0000),
        ("NodeSocketGeometry", "horizontal_edge", None),
    ])

    multiply_add = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["door_width"], 2: 0.0010}, attrs={"operation": "MULTIPLY_ADD"})
    multiply = nw.new_node(Nodes.Math, input_kwargs={0: multiply_add, 1: -1.0000}, attrs={"operation": "MULTIPLY"})
    transform_7 = nw.new_node(Nodes.Transform, input_kwargs={
        "Geometry": group_input.outputs["horizontal_edge"], "Translation": (0.0000, -0.0001, 0.0000), "Scale": (0.9999, 1.0000, 1.0000)})

    add = nw.new_node(Nodes.Math, input_kwargs={0: multiply_add, 1: -0.0001})
    add_1 = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["door_height"], 1: 0.0001})
    combine_xyz_2 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": add, "Z": add_1})
    transform_3 = nw.new_node(Nodes.Transform, input_kwargs={
        "Geometry": transform_7, "Translation": combine_xyz_2, "Rotation": (0.0000, -1.5708, 0.0000)})

    add_2 = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: 0.0001})
    combine_xyz_1 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": add_2})
    transform_2 = nw.new_node(Nodes.Transform, input_kwargs={
        "Geometry": transform_7, "Translation": combine_xyz_1, "Rotation": (0.0000, 1.5708, 0.0000)})

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_add})
    transform = nw.new_node(Nodes.Transform, input_kwargs={
        "Geometry": group_input.outputs["vertical_edge"], "Translation": combine_xyz})

    transform_1 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": transform, "Scale": (-1.0000, 1.0000, 1.0000)})

    convex_hull_final = nw.new_node(Nodes.ConvexHull, input_kwargs={"Geometry": transform})
    convex_hull_final1 = nw.new_node(Nodes.ConvexHull, input_kwargs={"Geometry": transform_1})
    convex_hull_final2 = nw.new_node(Nodes.ConvexHull, input_kwargs={"Geometry": transform_2})
    convex_hull_final3 = nw.new_node(Nodes.ConvexHull, input_kwargs={"Geometry": transform_3})

    join_geometry_1 = nw.new_node(Nodes.JoinGeometry, input_kwargs={
        "Geometry": [convex_hull_final, convex_hull_final1, convex_hull_final2, convex_hull_final3]})

    flip_faces = nw.new_node(Nodes.FlipFaces, input_kwargs={"Mesh": join_geometry_1})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Value": multiply, "Geometry": flip_faces})

def geometry_door_nodes(nw: NodeWrangler, **kwargs):
    door_height = nw.val(kwargs["door_height"])
    door_edge_thickness_2 = nw.val(kwargs["edge_thickness_2"])
    door_edge_width = nw.val(kwargs["edge_width"])
    door_edge_thickness_1 = nw.val(kwargs["edge_thickness_1"])
    door_edge_ramp_angle = nw.val(kwargs["edge_ramp_angle"])

    _re = nodegroup_ramped_edge().name
    re_kwargs = {"thickness_2": door_edge_thickness_2, "width": door_edge_width, "thickness_1": door_edge_thickness_1, "ramp_angle": door_edge_ramp_angle}
    ramped_edge = nw.new_node(_re, input_kwargs={"height": door_height, **re_kwargs})
    door_width = nw.val(kwargs["door_width"])
    ramped_edge_1 = nw.new_node(_re, input_kwargs={"height": door_width, **re_kwargs})
    panel_edge_frame = nw.new_node(nodegroup_panel_edge_frame().name, input_kwargs={
        "vertical_edge": ramped_edge, "door_width": door_width, "door_height": door_height, "horizontal_edge": ramped_edge_1})

    add = nw.new_node(Nodes.Math, input_kwargs={0: panel_edge_frame.outputs["Value"], 1: 0.0001})
    mid_board_thickness = nw.val(kwargs["board_thickness"])

    if kwargs["has_mid_ramp"]:
        mid_board = nw.new_node(nodegroup_mid_board().name,
            input_kwargs={"height": door_height, "thickness": mid_board_thickness, "width": door_width})
    else:
        mid_board = nw.new_node(nodegroup_mid_board_001().name,
            input_kwargs={"height": door_height, "thickness": mid_board_thickness, "width": door_width})

    combine_xyz_5 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": add, "Y": -0.0001, "Z": mid_board.outputs["mid_height"]})

    frame = [panel_edge_frame.outputs["Geometry"]]
    if kwargs["has_mid_ramp"]:
        double_rampled_edge = nw.new_node(nodegroup_double_rampled_edge().name,
            input_kwargs={"height": door_width, **re_kwargs})
        transform_5 = nw.new_node(Nodes.Transform, input_kwargs={
            "Geometry": double_rampled_edge, "Translation": combine_xyz_5, "Rotation": (0.0000, 1.5708, 0.0000)})
        convex_hull_midboard = nw.new_node(Nodes.ConvexHull, input_kwargs={"Geometry": transform_5})
        frame.append(nw.new_node(Nodes.FlipFaces, input_kwargs={"Mesh": convex_hull_midboard}))

    join_geometry_1 = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": frame})

    knob_raduis = nw.val(kwargs["knob_R"])
    know_length = nw.val(kwargs["knob_length"])
    multiply = nw.new_node(Nodes.Math, input_kwargs={0: door_height}, attrs={"operation": "MULTIPLY"})

    knob_handle = nw.new_node(nodegroup_knob_handle().name, input_kwargs={
        "Radius": knob_raduis, "thickness_1": door_edge_thickness_1, "thickness_2": door_edge_thickness_2,
        "length": know_length, "knob_mid_height": multiply, "edge_width": door_edge_width, "door_width": door_width})
    knob_flip_faces = nw.new_node(Nodes.FlipFaces, input_kwargs={"Mesh": knob_handle})

    _ng = nodegroup_node_group().name
    attach_gadgets = [
        nw.new_node(_ng, input_kwargs={"attach_height": nw.val(h), "door_width": door_width})
        for h in kwargs["attach_height"]
    ]

    flip_faces_middle = nw.new_node(Nodes.FlipFaces, input_kwargs={"Mesh": mid_board.outputs["Geometry"]})

    geos = [join_geometry_1, knob_flip_faces, flip_faces_middle] + attach_gadgets
    join_geometry = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": geos})

    multiply = nw.new_node(Nodes.Math, input_kwargs={0: door_width, 1: -0.5000}, attrs={"operation": "MULTIPLY"})

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply})

    transform = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": join_geometry, "Translation": combine_xyz})

    realize_instances_1 = nw.new_node(Nodes.RealizeInstances, input_kwargs={"Geometry": transform})

    triangulate = nw.new_node("GeometryNodeTriangulate", input_kwargs={"Mesh": realize_instances_1})
    transform_1 = nw.new_node(Nodes.Transform, input_kwargs={
        "Geometry": triangulate, "Scale": (-1.0 if kwargs["door_left_hinge"] else 1.0, 1.0000, 1.0000)})

    transform_2 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": transform_1, "Rotation": (0.0000, 0.0000, -1.5708)})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": transform_2})

# Parameter helpers

def update_translation_params(params):
    cell_widths = params["shelf_cell_width"]
    cell_heights = params["shelf_cell_height"]
    side_thickness = params["side_board_thickness"]
    div_thickness = params["division_board_thickness"]

    width = (len(cell_widths) - 1) * side_thickness * 2 + (len(cell_widths) - 1) * 0.001 + sum(cell_widths)
    height = (len(cell_heights) + 1) * div_thickness + params["bottom_board_height"] + sum(cell_heights)

    params["shelf_width"] = width
    params["shelf_height"] = height

    dist = -(width + side_thickness) / 2.0
    side_board_x_translation = [dist]
    for w in cell_widths:
        dist += side_thickness + w
        side_board_x_translation.append(dist)
        dist += side_thickness + 0.001
        side_board_x_translation.append(dist)
    side_board_x_translation = side_board_x_translation[:-1]

    d = params["bottom_board_height"] + div_thickness / 2.0
    division_board_z_translation = [d := d + h + div_thickness for h in [-div_thickness] + cell_heights]

    division_board_x_translation = [
        (side_board_x_translation[2 * i] + side_board_x_translation[2 * i + 1]) / 2.0
        for i in range(len(cell_widths))
    ]

    params["side_board_x_translation"] = side_board_x_translation
    params["division_board_x_translation"] = division_board_x_translation
    params["division_board_z_translation"] = division_board_z_translation
    params["bottom_gap_x_translation"] = division_board_x_translation
    return params

# Build

def build(seed=SEED):
    seed = int(seed)
    derived = abs(int(hashlib.md5(f"{seed}0".encode()).hexdigest(), 16)) % (2**32 - 1)
    random.seed(derived)
    np.random.seed(derived)

    # Consume 3 RNG values (original CabinetFactory.sample_params, results discarded)
    uniform(0.25, 0.35); uniform(0.3, 0.7); uniform(0.9, 1.8)

    # RNG: material selection under FixedSeed (save/restore state)
    py_st, np_st = random.getstate(), np.random.get_state()
    random.seed(int(seed)); np.random.seed(int(seed))
    np.random.choice(3, p=[0.5, 0.2, 0.3])  # was mat_name
    random.setstate(py_st); np.random.set_state(np_st)

    # Shelf cell layout
    shelf_cell_width = [
        np.random.choice([0.76, 0.36], p=[0.5, 0.5])
        * np.clip(normal(1.0, 0.1), 0.75, 1.25)
    ]
    num_v_cells = randint(3, 7)
    shelf_cell_height = [
        0.3 * np.clip(normal(1.0, 0.06), 0.75, 1.25) for _ in range(num_v_cells)
    ]

    # Shelf detail params
    shelf_params = {
        "shelf_cell_width": shelf_cell_width,
        "shelf_cell_height": shelf_cell_height,
        "shelf_depth": np.clip(normal(0.26, 0.03), 0.18, 0.36),
        "side_board_thickness": np.clip(normal(0.02, 0.002), 0.015, 0.025),
        "backboard_thickness": 0.01,
        "bottom_board_y_gap": uniform(0.01, 0.05),
        "bottom_board_height": np.clip(normal(0.083, 0.01), 0.05, 0.11) * np.random.choice([1.0, 0.0], p=[0.8, 0.2]),
        "division_board_thickness": np.clip(normal(0.02, 0.002), 0.015, 0.025),
        "screw_depth_head": uniform(0.001, 0.004),
        "screw_head_radius": uniform(0.001, 0.004),
        "screw_width_gap": uniform(0.0, 0.02),
        "screw_depth_gap": uniform(0.025, 0.06),
    }
    # RNG: consume attach_length/width/thickness/gap (values unused)
    uniform(0.05, 0.1); uniform(0.01, 0.025); uniform(0.002, 0.005); uniform(0.0, 0.05)
    update_translation_params(shelf_params)

    # Create shelf
    shelf = make_geo_object(geometry_nodes, shelf_params)

    # Door dimensions from shelf
    shelf_width_total = shelf_params["shelf_width"] + shelf_params["side_board_thickness"] * 2
    if shelf_width_total < 0.55:
        door_width, num_door = shelf_width_total, 1
    else:
        door_width, num_door = shelf_width_total / 2.0 - 0.0005, 2

    door_height = (
        shelf_params["division_board_z_translation"][-1]
        - shelf_params["division_board_z_translation"][0]
        + shelf_params["division_board_thickness"]
    )
    if len(shelf_params["division_board_z_translation"]) > 5 and np.random.choice([True, False], p=[0.5, 0.5]):
        door_height = (
            shelf_params["division_board_z_translation"][3]
            - shelf_params["division_board_z_translation"][0]
            + shelf_params["division_board_thickness"]
        )

    # Door detail params (RNG order must match original CabinetDoorBaseFactory.get_asset_params)
    edge_thickness_1 = uniform(0.01, 0.02)
    edge_width = uniform(0.03, 0.05)
    edge_thickness_2 = uniform(0.005, 0.01)
    edge_ramp_angle = uniform(0.6, 0.8)
    knob_R = uniform(0.003, 0.006)
    knob_length = uniform(0.018, 0.035)
    attach_gap_door = uniform(0.05, 0.15)
    door_attach_height = [attach_gap_door, door_height - attach_gap_door]
    has_mid_ramp = bool(np.random.choice([True, False], p=[0.6, 0.4]))
    if has_mid_ramp:
        np.random.choice(2, p=[0.6, 0.4])  # RNG: was board material lower
        np.random.choice(2, p=[0.6, 0.4])  # RNG: was board material upper

    door_params = {
        "door_width": door_width,
        "door_height": door_height,
        "edge_thickness_1": edge_thickness_1,
        "edge_width": edge_width,
        "edge_thickness_2": edge_thickness_2,
        "edge_ramp_angle": edge_ramp_angle,
        "board_thickness": edge_thickness_1 - 0.005,
        "knob_R": knob_R,
        "knob_length": knob_length,
        "attach_height": door_attach_height,
        "has_mid_ramp": has_mid_ramp,
        "door_left_hinge": False,
    }

    # Create right door, then left (mirrored)
    right_door = make_geo_object(geometry_door_nodes, door_params)
    door_params["door_left_hinge"] = True
    left_door = make_geo_object(geometry_door_nodes, door_params)

    # Position doors at hinges
    sd = shelf_params["shelf_depth"] / 2.0
    sw = shelf_params["shelf_width"] / 2.0
    bbh = shelf_params["bottom_board_height"]
    if num_door == 1:
        hinges = [(sd + 0.0025, -shelf_width_total / 2.0, bbh)]
        attpos = [(sd, -sw, bbh + z) for z in door_attach_height]
    else:
        hinges = [(sd + 0.008, -shelf_width_total / 2.0, bbh), (sd + 0.008, shelf_width_total / 2.0, bbh)]
        attpos = [(sd, -sw, bbh + z) for z in door_attach_height] + [(sd, sw, bbh + z) for z in door_attach_height]

    for door, hp in zip([right_door, left_door], hinges):
        door.location = (float(hp[0]), float(hp[1]), float(hp[2]))
        apply_transform(door, loc=True, rot=True, scale=True)

    # Hinge geometry
    attach_objs = []
    for pos in attpos:
        bpy.ops.mesh.primitive_cube_add(size=0.02, location=(float(pos[0]), float(pos[1]), float(pos[2])))
        att = bpy.context.active_object
        att.scale = (0.03, 1.0, 2.25)
        apply_transform(att)
        attach_objs.append(att)

    # --- Per-part material binding (BEFORE join) ---
    # cabinet.py applies frame_material (wood) to shelf/door/frame parts
    # and metal (get_shelf_material("metal")) to attach/hardware at lines 1259, 1381.
    # Since bmesh-level join drops material slots, we track face-index ranges per
    # source component and set poly.material_index on the joined mesh afterwards.
    frame_parts = [shelf, right_door, left_door]
    metal_parts = list(attach_objs)

    # Join all via bmesh, tracking face counts per component for post-join
    # material_index assignment.
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    frame_face_count = 0
    for comp in frame_parts:
        eval_obj = comp.evaluated_get(dg)
        me_temp = eval_obj.to_mesh()
        me_temp.transform(comp.matrix_world)
        before = len(bm.faces)
        bm.from_mesh(me_temp)
        after = len(bm.faces)
        frame_face_count += (after - before)
        eval_obj.to_mesh_clear()
    metal_face_count = 0
    for comp in metal_parts:
        eval_obj = comp.evaluated_get(dg)
        me_temp = eval_obj.to_mesh()
        me_temp.transform(comp.matrix_world)
        before = len(bm.faces)
        bm.from_mesh(me_temp)
        after = len(bm.faces)
        metal_face_count += (after - before)
        eval_obj.to_mesh_clear()

    new_mesh = bpy.data.meshes.new("CabinetFactory")
    bm.to_mesh(new_mesh)
    bm.free()
    obj = bpy.data.objects.new("CabinetFactory", new_mesh)
    bpy.context.collection.objects.link(obj)

    # Attach both material slots: frame (slot 0) + metal (slot 1).
    if MAT_FRAME is not None:
        obj.data.materials.append(MAT_FRAME)
    if MAT_METAL is not None:
        obj.data.materials.append(MAT_METAL)

    # Assign metal material_index to the attach-hardware face range.
    if MAT_METAL is not None and metal_face_count > 0:
        for i, poly in enumerate(obj.data.polygons):
            if i >= frame_face_count:
                poly.material_index = 1

    for comp in [shelf, right_door, left_door] + attach_objs:
        bpy.data.objects.remove(comp, do_unlink=True)

    # (speculative wear_tear removed — cabinet.py does not apply scratches/edge_wear)
    return obj

build(SEED)

