# [FL_INDEX: keywords="blender_factory, procedural_3d, TriangleShelfFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: TriangleShelfFactory | Category: factories_tex
# Prompt: A 3D model of a triangular corner shelf unit rendered from a three-quarter perspective, featuring three triangular shelves stacked vertically and connected by vertical support posts at each corner, with a metallic frame and dark-colored shelf surfaces.

"""TriangleShelfFactory — textured conversion.

Geometry copied verbatim from objects_blender/shelves/TriangleShelfFactory.py.
keys "white", "black_wood", "wood" (the three keys used by
TriangleShelfBaseFactory.get_asset_params).

Shader sources inlined here (raw bpy node tree translation):
  - shader_shelves_white               -> make_shelves_white
  - shader_shelves_black_wood          -> make_shelves_black_wood   (supports z_axis_texture)
  - shader_shelves_wood                -> make_shelves_wood         (supports z_axis_texture)
  - shader_rough_plastic (white alt)   -> make_plastic_rough
  - shader_wood (black_wood/wood alt)  -> make_wood

triangle_shelf.py does NOT implement finalize_assets() and does
not apply wear_tear, so no scratches/edge_wear stage is needed here.
"""


import os
import math
import random
import colorsys

import bpy
import bmesh
import numpy as np
from numpy.random import normal, uniform

# Sources faithfully translated from:
#       shader_shelves_white, shader_shelves_black_wood, shader_shelves_wood
# MusgraveTexture (removed in Blender 5.0) is replaced with stretched NoiseTexture
# in the same topology as the original nodes.

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

def _rgba_mix(nt, factor, a_socket_or_color, b_socket_or_color):
    """Create RGBA Mix node, returning the node (outputs[2] == Result)."""

    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    # Factor
    if hasattr(factor, "links") or hasattr(factor, "default_value"):
        if hasattr(factor, "links"):
            nt.links.new(factor, mix.inputs[0])
        else:
            mix.inputs[0].default_value = factor
    else:
        mix.inputs[0].default_value = float(factor)
    # A = inputs[6], B = inputs[7]
    for idx, src in ((6, a_socket_or_color), (7, b_socket_or_color)):
        if hasattr(src, "links"):
            nt.links.new(src, mix.inputs[idx])
        else:
            mix.inputs[idx].default_value = src
    return mix

# ----------------------------------------------------------------------------
# Shelves-white: flat principled
# ----------------------------------------------------------------------------
def _shelves_white_sampler():
    v = float(np.random.uniform(0.7, 1.0))
    rgb = [
        v * (1.0 + float(np.random.normal(0, 0.005))),
        v * (1.0 + float(np.random.normal(0, 0.005))),
        v * (1.0 + float(np.random.normal(0, 0.005))),
    ]
    return dict(rgb=rgb, roughness=float(np.random.uniform(0.7, 1.0)))

def make_shelves_white(name="ShelvesWhite", **kwargs) -> bpy.types.Material:
    params = _shelves_white_sampler()
    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{
        "Base Color": (*params["rgb"], 1.0),
        "Roughness": params["roughness"],
    })
    _connect_output(nt, bsdf)
    return mat

# ----------------------------------------------------------------------------
# Shelves-black-wood: full procedural wood grain with optional z-axis texture
# ----------------------------------------------------------------------------
def _shelves_black_wood_sampler():
    return dict(
        wave_scale=float(np.random.uniform(1.0, 3.0)),
        dark_scale=float(np.random.uniform(0.0, 0.01)),
        gray_scale=float(np.random.uniform(0.01, 0.03)),
        rgb=[
            float(np.random.uniform(0.015, 0.035)),
            float(np.random.uniform(0.0, 0.01)),
            float(np.random.uniform(0.0, 0.01)),
        ],
        roughness=float(np.random.uniform(0.75, 1.0)),
    )

def make_shelves_black_wood(name="ShelvesBlackWood", z_axis_texture=False,
                            **kwargs) -> bpy.types.Material:
    """Raw-bpy port of shader_shelves_black_wood in plywood.py."""

    params = _shelves_black_wood_sampler()
    wave_scale = params["wave_scale"]
    if z_axis_texture:
        wave_scale_vec = (wave_scale, wave_scale, 0.1)
        mapping1_scale = (0.1, 0.1, 2.0)
    else:
        wave_scale_vec = (wave_scale, 0.1, 0.1)
        mapping1_scale = (0.1, 2.0, 2.0)

    mat = _new_material(name)
    nt = mat.node_tree

    # ---- First texture chain (voronoi-on-noise, colorramp_1) ----
    tex_coord_1 = nt.nodes.new("ShaderNodeTexCoord")
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    mapping_1.inputs["Scale"].default_value = mapping1_scale
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
    voronoi_color_out = voronoi.outputs.get("Color") or voronoi.outputs[0]
    nt.links.new(voronoi_color_out, (colorramp_1.inputs.get("Fac") or colorramp_1.inputs[0]))
    colorramp_1.color_ramp.elements[0].position = 0.0864
    colorramp_1.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    colorramp_1.color_ramp.elements[1].position = 0.1091
    colorramp_1.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # ---- Second texture chain (wave / musgrave-substitute / colorramp_2) ----
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = wave_scale_vec
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    # Musgrave substitute: second noise fed by first noise's Fac
    musgrave_sub = nt.nodes.new("ShaderNodeTexNoise")
    musgrave_sub.inputs["Scale"].default_value = 20.0
    if "Detail" in musgrave_sub.inputs: musgrave_sub.inputs["Detail"].default_value = 3.0
    nt.links.new(_noise_fac_output(noise), musgrave_sub.inputs["Vector"])

    # mix_1 = RGBA mix of musgrave-sub (fac) and noise color
    noise_color_out = noise.outputs.get("Color") or noise.outputs[0]
    mix_1 = _rgba_mix(nt, 0.5, _noise_fac_output(musgrave_sub), noise_color_out)

    colorramp_2 = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(mix_1.outputs[2], (colorramp_2.inputs.get("Fac") or colorramp_2.inputs[0]))
    colorramp_2.color_ramp.elements[0].position = 0.0818
    colorramp_2.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    colorramp_2.color_ramp.elements[1].position = 0.8500
    colorramp_2.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # ---- Combine chains: mix_2 (fac=0.6), base colorramp, mix_3 (fac=0.004) ----
    mix_2 = _rgba_mix(nt, 0.6, colorramp_1.outputs["Color"], colorramp_2.outputs["Color"])

    dark_scale = params["dark_scale"]
    gray_scale = params["gray_scale"]
    color_scale = (*params["rgb"], 1.0)

    colorramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(mix_2.outputs[2], (colorramp.inputs.get("Fac") or colorramp.inputs[0]))
    colorramp.color_ramp.elements.new(0)
    colorramp.color_ramp.elements[0].position = 0.15
    colorramp.color_ramp.elements[0].color = (dark_scale, dark_scale, dark_scale, 1.0)
    colorramp.color_ramp.elements[1].position = 0.5
    colorramp.color_ramp.elements[1].color = (gray_scale, gray_scale, gray_scale, 1.0)
    colorramp.color_ramp.elements[2].position = 1.0
    colorramp.color_ramp.elements[2].color = color_scale

    mix_3 = _rgba_mix(nt, 0.0040,
                      colorramp_1.outputs["Color"],
                      colorramp_2.outputs["Color"])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.01
    nt.links.new(mix_3.outputs[2], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(colorramp.outputs["Color"], bsdf.inputs["Base Color"])
    _set_principled(bsdf, Roughness=params["roughness"])

    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# ----------------------------------------------------------------------------
# Shelves-wood (blonde): same topology as black_wood but HSV ramp
# ----------------------------------------------------------------------------
def _shelves_wood_sampler():
    return dict(
        bright_hsv=[float(np.random.uniform(0.03, 0.09)),
                    float(np.random.uniform(0.5, 0.7)),
                    float(np.random.uniform(0.7, 1.0))],
        mid_hsv=[float(np.random.uniform(0.02, 0.06)),
                 float(np.random.uniform(0.6, 1.0)),
                 float(np.random.uniform(0.3, 0.6))],
        dark_hsv=[float(np.random.uniform(0.03, 0.05)),
                  float(np.random.uniform(0.6, 1.0)),
                  float(np.random.uniform(0.1, 0.3))],
        wave_scale=float(np.random.uniform(1.0, 3.0)),
        roughness=float(np.random.uniform(0.75, 1.0)),
    )

def make_shelves_wood(name="ShelvesWood", z_axis_texture=False,
                      **kwargs) -> bpy.types.Material:
    """Raw-bpy port of shader_shelves_wood in plywood.py (blonde variant)."""

    params = _shelves_wood_sampler()
    wave_scale = params["wave_scale"]
    if z_axis_texture:
        wave_scale_vec = (wave_scale, wave_scale, 0.1)
        mapping1_scale = (0.1, 0.1, 2.0)
    else:
        wave_scale_vec = (wave_scale, 0.1, 0.1)
        mapping1_scale = (0.1, 2.0, 2.0)

    mat = _new_material(name)
    nt = mat.node_tree

    # First texture chain (voronoi-on-noise)
    tex_coord_1 = nt.nodes.new("ShaderNodeTexCoord")
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    mapping_1.inputs["Scale"].default_value = mapping1_scale
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
    voronoi_color_out = voronoi.outputs.get("Color") or voronoi.outputs[0]
    nt.links.new(voronoi_color_out, (colorramp_1.inputs.get("Fac") or colorramp_1.inputs[0]))
    colorramp_1.color_ramp.elements[0].position = 0.0864
    colorramp_1.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    colorramp_1.color_ramp.elements[1].position = 0.1091
    colorramp_1.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # Second chain (wave + musgrave-substitute)
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = wave_scale_vec
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    musgrave_sub = nt.nodes.new("ShaderNodeTexNoise")
    musgrave_sub.inputs["Scale"].default_value = 20.0
    if "Detail" in musgrave_sub.inputs: musgrave_sub.inputs["Detail"].default_value = 3.0
    nt.links.new(_noise_fac_output(noise), musgrave_sub.inputs["Vector"])

    noise_color_out = noise.outputs.get("Color") or noise.outputs[0]
    mix_1 = _rgba_mix(nt, 0.5, _noise_fac_output(musgrave_sub), noise_color_out)

    colorramp_2 = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(mix_1.outputs[2], (colorramp_2.inputs.get("Fac") or colorramp_2.inputs[0]))
    colorramp_2.color_ramp.elements[0].position = 0.0818
    colorramp_2.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    colorramp_2.color_ramp.elements[1].position = 0.8500
    colorramp_2.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    mix_2 = _rgba_mix(nt, 0.6, colorramp_1.outputs["Color"], colorramp_2.outputs["Color"])

    # Blonde HSV ramp (dark -> mid -> bright)
    colorramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(mix_2.outputs[2], (colorramp.inputs.get("Fac") or colorramp.inputs[0]))
    colorramp.color_ramp.elements.new(0)
    colorramp.color_ramp.elements[0].position = 0.02
    colorramp.color_ramp.elements[0].color = hsv2rgba(params["dark_hsv"])
    colorramp.color_ramp.elements[1].position = 0.11
    colorramp.color_ramp.elements[1].color = hsv2rgba(params["mid_hsv"])
    colorramp.color_ramp.elements[2].position = 0.8
    colorramp.color_ramp.elements[2].color = hsv2rgba(params["bright_hsv"])

    mix_3 = _rgba_mix(nt, 0.0040,
                      colorramp_1.outputs["Color"],
                      colorramp_2.outputs["Color"])
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.01
    nt.links.new(mix_3.outputs[2], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(colorramp.outputs["Color"], bsdf.inputs["Base Color"])
    _set_principled(bsdf, Roughness=params["roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# ----------------------------------------------------------------------------
# plastic_rough (white alt) — raw-bpy port of plastic_rough.py:shader_rough_plastic
# ----------------------------------------------------------------------------
def make_plastic_rough(name="PlasticRough", **kwargs) -> bpy.types.Material:
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

    mul1 = nt.nodes.new("ShaderNodeMath"); mul1.operation = "MULTIPLY"
    mul1.inputs[1].default_value = 0.4
    nt.links.new(map_range.outputs["Result"], mul1.inputs[0])
    mul2 = nt.nodes.new("ShaderNodeMath"); mul2.operation = "MULTIPLY"
    nt.links.new(_noise_fac_output(noise), mul2.inputs[0])
    nt.links.new(mul1.outputs[0], mul2.inputs[1])
    mul3 = nt.nodes.new("ShaderNodeMath"); mul3.operation = "MULTIPLY"
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
# generic wood (black_wood / wood 40% alt) — port of wood.py:shader_wood
# ----------------------------------------------------------------------------
def make_wood(name="Wood", **kwargs) -> bpy.types.Material:
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
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# ----------------------------------------------------------------------------
# Registry — mirrors get_shelf_material() branches in plywood.py
# ----------------------------------------------------------------------------
REGISTRY = {
    # plywood.py:469-472 — white => 0.6 shelves_white, 0.4 rough_plastic
    "white":      [(make_shelves_white, 0.6), (make_plastic_rough, 0.4)],
    # plywood.py:473-476 — black_wood => 0.6 shelves_black_wood, 0.4 shader_wood
    "black_wood": [(make_shelves_black_wood, 0.6), (make_wood, 0.4)],
    # plywood.py:477-480 — wood => 0.6 shelves_wood, 0.4 shader_wood
    "wood":       [(make_shelves_wood, 0.6), (make_wood, 0.4)],
}

def get_shelf_material(key: str, name: str = None, z_axis_texture=False):
    """Mirror of plywood.py:get_shelf_material() random-branch selection."""
    # IMPORTANT: mirror the exact np.random.choice call in plywood.py to keep
    from numpy.random import choice as np_choice
    if key == "white":
        ctors_p = [(make_shelves_white, 0.6), (make_plastic_rough, 0.4)]
    elif key == "black_wood":
        ctors_p = [(make_shelves_black_wood, 0.6), (make_wood, 0.4)]
    elif key == "wood":
        ctors_p = [(make_shelves_wood, 0.6), (make_wood, 0.4)]
    else:
        raise KeyError(key)
    ctors = [c for c, _ in ctors_p]
    probs = np.array([p for _, p in ctors_p], dtype=float)
    idx = int(np_choice(len(ctors), p=probs / probs.sum()))
    return ctors[idx](name=name or key, z_axis_texture=z_axis_texture)

# --- Geometry code (copied verbatim from
#     objects_blender/shelves/TriangleShelfFactory.py, lines 1-140) ===========

SEED = int(os.environ.get('SEED', 0))
np.random.seed(SEED)

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    bpy.context.scene.cursor.location = (0, 0, 0)

def add_box(cx, cy, cz, sx, sy, sz):
    """Axis-aligned cuboid."""

    bpy.ops.mesh.primitive_cube_add(location=(cx, cy, cz))
    obj = bpy.context.active_object
    obj.scale = (sx / 2, sy / 2, sz / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj

def add_triangular_board(bw, thickness, z_center):
    """Build a right-triangle shelf board: vertices at (0,0), (bw,0), (0,bw)."""

    verts = [
        (0,  0,  z_center - thickness / 2),
        (bw, 0,  z_center - thickness / 2),
        (0,  bw, z_center - thickness / 2),
        (0,  0,  z_center + thickness / 2),
        (bw, 0,  z_center + thickness / 2),
        (0,  bw, z_center + thickness / 2),
    ]
    faces = [
        (0, 1, 2),           # bottom
        (3, 5, 4),           # top (reversed winding)
        (0, 3, 4, 1),        # front (y=0)
        (1, 4, 5, 2),        # hypotenuse
        (2, 5, 3, 0),        # left (x=0)
    ]
    mesh = bpy.data.meshes.new('tri_board')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new('tri_board', mesh)
    bpy.context.collection.objects.link(obj)
    return obj

def join_all(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    result = bpy.context.active_object
    result.name = name
    return result

def sample_triangle_shelf_params():
    """Sample parameters"""

    leg_board_gap = uniform(0.002, 0.005)
    leg_width = uniform(0.01, 0.03)
    leg_depth = uniform(0.01, 0.02)
    leg_length = float(np.clip(normal(0.6, 0.05), 0.45, 0.75))
    board_thickness = uniform(0.01, 0.025)
    board_width = float(np.clip(normal(0.3, 0.03), 0.2, 0.4))
    board_extrude_length = uniform(0.03, 0.07)
    side_board_height = uniform(0.02, 0.04)
    bottom_layer_height = uniform(0.05, 0.1)
    top_layer_height = leg_length - uniform(0.02, 0.07)
    mid_layer_height = (top_layer_height + bottom_layer_height) / 2.0

    return {
        'leg_width': leg_width,
        'leg_depth': leg_depth,
        'leg_length': leg_length,
        'board_thickness': board_thickness,
        'board_width': board_width,
        'bottom_layer_height': bottom_layer_height,
        'mid_layer_height': mid_layer_height,
        'top_layer_height': top_layer_height,
    }

def build_triangle_shelf(p, mat_board=None, mat_leg=None):
    """Build a triangular corner shelf from sampled parameters."""

    bw = p['board_width']
    bt = p['board_thickness']
    ll = p['leg_length']
    lw = p['leg_width']
    ld = p['leg_depth']

    board_parts = []
    leg_parts = []

    # Three triangular shelves at bottom / mid / top heights
    for z in (p['bottom_layer_height'], p['mid_layer_height'], p['top_layer_height']):
        board_parts.append(add_triangular_board(bw, bt, z))

    # Top cap shelf (one extra at the top of the legs)
    board_parts.append(add_triangular_board(bw, bt, ll))

    # Two perpendicular leg walls (forming a right angle at origin)
    leg_parts.append(add_box(bw / 2, 0, ll / 2, bw, ld, ll))
    leg_parts.append(add_box(0, bw / 2, ll / 2, ld, bw, ll))

    # Center corner leg (at origin, both walls meet)
    leg_parts.append(add_box(lw / 2, lw / 2, ll / 2, lw, lw, ll))

    # triangle_shelf.py:1357-1362: board_material on boards, leg_material
    # (with z_axis_texture=True) on legs) ----
    if mat_board is not None:
        for b in board_parts:
            b.data.materials.append(mat_board)
    if mat_leg is not None:
        for l in leg_parts:
            l.data.materials.append(mat_leg)

    return join_all(board_parts + leg_parts, 'TriangleShelfFactory')

# each first the discrete ["black_wood"/"wood"/"white"] choice (p=[0.2,0.6,0.2]),
# then get_shelf_material() (which internally does another np.random.choice).
# leg_material gets z_axis_texture=True.
seed_all(SEED)

# Clean scene first so material reuse across re-invocations is clean
for _obj in list(bpy.data.objects):
    bpy.data.objects.remove(_obj, do_unlink=True)
for _m in list(bpy.data.meshes):
    bpy.data.meshes.remove(_m)
for _mat in list(bpy.data.materials):
    bpy.data.materials.remove(_mat)
bpy.context.scene.cursor.location = (0, 0, 0)

_board_key = str(np.random.choice(["black_wood", "wood", "white"], p=[0.2, 0.6, 0.2]))
_leg_key   = str(np.random.choice(["black_wood", "wood", "white"], p=[0.2, 0.6, 0.2]))
MAT_BOARD  = get_shelf_material(_board_key, name="BoardMat", z_axis_texture=False)
MAT_LEG    = get_shelf_material(_leg_key,   name="LegMat",   z_axis_texture=True)

# Main
def build(seed=SEED):
    global SEED
    SEED = seed
    np.random.seed(seed)
    # DO NOT clear scene here (that would delete Phase-1 materials) — only wipe
    # geometry, keeping materials cached in MAT_BOARD / MAT_LEG.
    for _obj in list(bpy.data.objects):
        bpy.data.objects.remove(_obj, do_unlink=True)
    for _m in list(bpy.data.meshes):
        bpy.data.meshes.remove(_m)
    bpy.context.scene.cursor.location = (0, 0, 0)

    params = sample_triangle_shelf_params()
    return build_triangle_shelf(params, mat_board=MAT_BOARD, mat_leg=MAT_LEG)

build(SEED)

