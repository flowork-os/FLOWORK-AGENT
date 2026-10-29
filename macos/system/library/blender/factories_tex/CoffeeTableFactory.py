# [FL_INDEX: keywords="blender_factory, procedural_3d, CoffeeTableFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: CoffeeTableFactory | Category: factories_tex
# Prompt: A 3D model of a low-profile coffee table rendered from an elevated three-quarter perspective, featuring a wide rectangular top with rounded corners, a matching bottom shelf, and two short pedestal legs with flared circular bases connecting the two surfaces.

"""CoffeeTableFactory (textured) -- raw-bpy port of
faithful inlined shaders translated from:

Material sampling order mirrors TableDiningFactory.get_material_params (dining_table.py:210-222):
  1. TopMaterial = weighted_sample(table_top)()   -- table_top registry
  2. LegMaterial = weighted_sample(tableware)()   -- tableware registry
  3. scratch probability gate (consumed but NOT applied)
  4. edge_wear probability gate (consumed but NOT applied)

dining_table.py finalize_assets (line 333-338) is `pass` (wear_tear commented out)
-> NO wear_tear is applied. Gates are consumed for RNG alignment only.

Geometry is taken verbatim from objects_blender/tables/CoffeeTableFactory.py,
with GeometryNodeSetMaterial nodes inserted before the final join.
"""


import os
import math
import random
import colorsys

import bpy
import numpy as np
from numpy.random import uniform

# --- Inlined material library (hand-crafted for CoffeeTableFactory) ---

def seed_all(seed):
    np.random.seed(int(seed))
    random.seed(int(seed))

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

def hsv2rgba(h, s, v):
    h = h - math.floor(h)
    s = float(max(0.0, min(1.0, s)))
    v = float(max(0.0, min(1.0, v)))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

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
    if np.random.uniform() < 0.2:
        return _metal_natural_hsv()
    return (np.random.uniform(0, 1),
            np.random.uniform(0.3, 0.6),
            _mat_log_uniform(0.02, 0.5))

def bark_hsv():
    hexval = WOOD_COLORS[np.random.randint(0, len(WOOD_COLORS))]
    return _rgb2hsv(_hex2rgba(hexval)[:3])

def weighted_sample_mat(registry):
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
        "Coat Roughness": ("Coat Roughness", "Clearcoat Roughness"),
        "Sheen Weight": ("Sheen Weight", "Sheen"),
        "Subsurface Weight": ("Subsurface Weight", "Subsurface"),
        "Transmission Weight": ("Transmission Weight", "Transmission"),
    }
    for k, v in kw.items():
        names = aliases.get(k, (k,))
        for name in names:
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = v
                break

def _noise_fac_output(noise_node):
    for k in ("Fac", "Factor"):
        if k in noise_node.outputs:
            return noise_node.outputs[k]
    return noise_node.outputs[0]

def _voronoi_distance_output(vor_node):
    if "Distance" in vor_node.outputs:
        return vor_node.outputs["Distance"]
    return vor_node.outputs[0]

def _set_noise_dims(node, dims):
    if hasattr(node, "noise_dimensions"):
        try:
            node.noise_dimensions = dims
            return
        except TypeError:
            pass
    if dims == "4D" and hasattr(node, "noise_dimensions"):
        try:
            node.noise_dimensions = "3D"
        except TypeError:
            pass

def _set_voronoi_dims(node, dims):
    if hasattr(node, "voronoi_dimensions"):
        try:
            node.voronoi_dimensions = dims
            return
        except TypeError:
            pass
    if dims == "4D" and hasattr(node, "voronoi_dimensions"):
        try:
            node.voronoi_dimensions = "3D"
        except TypeError:
            pass

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

def _connect_output(nt, bsdf, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    return out

# ----------------------------------------------------------------------------
# Material constructors: table_top registry
# ----------------------------------------------------------------------------

def make_marble(name="Marble"):
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    scale_vec = nt.nodes.new("ShaderNodeVectorMath")
    scale_vec.operation = "SCALE"
    nt.links.new(tex_coord.outputs["Object"], scale_vec.inputs[0])

    vector_rotate = nt.nodes.new("ShaderNodeVectorRotate")
    if hasattr(vector_rotate, "rotation_type"):
        try:
            vector_rotate.rotation_type = "EULER_XYZ"
        except TypeError:
            pass
    nt.links.new(scale_vec.outputs["Vector"], vector_rotate.inputs["Vector"])

    seed_val = nt.nodes.new("ShaderNodeValue")
    seed_val.label = "seed"
    seed_val.outputs[0].default_value = 0.0

    scale_val = nt.nodes.new("ShaderNodeValue")
    scale_val.label = "scale"
    scale_val.outputs[0].default_value = 3.0

    add_scale = nt.nodes.new("ShaderNodeMath")
    add_scale.operation = "ADD"
    nt.links.new(scale_val.outputs[0], add_scale.inputs[0])
    add_scale.inputs[1].default_value = 1.0

    noise_tex_2 = nt.nodes.new("ShaderNodeTexNoise")
    _set_noise_dims(noise_tex_2, "4D")
    nt.links.new(vector_rotate.outputs["Vector"], noise_tex_2.inputs["Vector"])
    if "W" in noise_tex_2.inputs:
        nt.links.new(seed_val.outputs[0], noise_tex_2.inputs["W"])
    nt.links.new(add_scale.outputs[0], noise_tex_2.inputs["Scale"])
    if "Detail" in noise_tex_2.inputs:
        noise_tex_2.inputs["Detail"].default_value = 15.0

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[1].default_value = 0.48
    map_range.inputs[2].default_value = 0.60
    nt.links.new(_noise_fac_output(noise_tex_2), map_range.inputs[0])

    noise_tex = nt.nodes.new("ShaderNodeTexNoise")
    _set_noise_dims(noise_tex, "4D")
    nt.links.new(vector_rotate.outputs["Vector"], noise_tex.inputs["Vector"])
    if "W" in noise_tex.inputs:
        nt.links.new(seed_val.outputs[0], noise_tex.inputs["W"])
    nt.links.new(scale_val.outputs[0], noise_tex.inputs["Scale"])
    if "Detail" in noise_tex.inputs:
        noise_tex.inputs["Detail"].default_value = 15.0

    noise_tex_3 = nt.nodes.new("ShaderNodeTexNoise")
    _set_noise_dims(noise_tex_3, "3D")
    nt.links.new(_noise_fac_output(noise_tex), noise_tex_3.inputs["Vector"])
    noise_tex_3.inputs["Scale"].default_value = 8.0
    if "Detail" in noise_tex_3.inputs:
        noise_tex_3.inputs["Detail"].default_value = 15.0

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    _set_voronoi_dims(voronoi, "4D")
    if hasattr(voronoi, "feature"):
        try:
            voronoi.feature = "DISTANCE_TO_EDGE"
        except TypeError:
            pass
    nt.links.new(_noise_fac_output(noise_tex_3), voronoi.inputs["Vector"])
    if "W" in voronoi.inputs:
        voronoi.inputs["W"].default_value = 1.64
    voronoi.inputs["Scale"].default_value = 3.0

    colorramp_edge = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = colorramp_edge.inputs.get("Fac") or colorramp_edge.inputs[0]
    nt.links.new(_voronoi_distance_output(voronoi), fac_in)
    colorramp_edge.color_ramp.elements[0].position = 0.0
    colorramp_edge.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    colorramp_edge.color_ramp.elements[1].position = 0.03
    colorramp_edge.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)

    mul_vein = nt.nodes.new("ShaderNodeMath")
    mul_vein.operation = "MULTIPLY"
    nt.links.new(map_range.outputs["Result"], mul_vein.inputs[0])
    nt.links.new(colorramp_edge.outputs["Color"], mul_vein.inputs[1])

    noise_tex_1 = nt.nodes.new("ShaderNodeTexNoise")
    _set_noise_dims(noise_tex_1, "4D")
    nt.links.new(_noise_fac_output(noise_tex), noise_tex_1.inputs["Vector"])
    if "W" in noise_tex_1.inputs:
        nt.links.new(seed_val.outputs[0], noise_tex_1.inputs["W"])
    noise_tex_1.inputs["Scale"].default_value = 8.0
    if "Detail" in noise_tex_1.inputs:
        noise_tex_1.inputs["Detail"].default_value = 15.0

    mix_noise = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_noise, "data_type"):
        mix_noise.data_type = "RGBA"
    mix_noise.inputs[0].default_value = 0.8
    nt.links.new(_noise_fac_output(noise_tex), mix_noise.inputs[6])
    nt.links.new(_noise_fac_output(noise_tex_1), mix_noise.inputs[7])

    colorramp_base = nt.nodes.new("ShaderNodeValToRGB")
    fac_in2 = colorramp_base.inputs.get("Fac") or colorramp_base.inputs[0]
    nt.links.new(mix_noise.outputs[2], fac_in2)
    colorramp_base.color_ramp.elements[0].position = 0.30
    colorramp_base.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    colorramp_base.color_ramp.elements[1].position = 0.90
    colorramp_base.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)

    mix_color = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_color, "data_type"):
        mix_color.data_type = "RGBA"
    nt.links.new(mul_vein.outputs[0], mix_color.inputs[0])
    nt.links.new(colorramp_base.outputs["Color"], mix_color.inputs[6])
    mix_color.inputs[7].default_value = (0.0376, 0.0179, 0.0033, 1.0)

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.02
    nt.links.new(mul_vein.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix_noise.outputs[2], bsdf.inputs["Base Color"])
    _set_principled(bsdf, **{"Specular IOR Level": 0.6, "Roughness": 0.1})

    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_tiled_wood(name="TiledWood"):
    """Uses BrickTexture for tiling and multi-layer noise/mix for wood grain.
    Original uses MusgraveTexture (removed in Blender 5.0) -- substituted
    with stretched NoiseTexture.
    """
    # Sample parameters that the original shader_wood_tiled samples:
    hscale = float(np.clip(np.random.normal(6, 4), 3, 9))
    vscale = float(np.random.uniform(0.05, 0.2)) * hscale
    seed_param = float(np.random.uniform(-1000.0, 1000.0))

    # get_color from wood.py
    bh, bs, bv = bark_hsv()
    base_color = hsv2rgba(
        bh + float(np.random.uniform(-0.0, 0.05)),
        bs + float(np.random.uniform(-0.3, 0.2)),
        bv * _mat_log_uniform(0.2, 20),
    )

    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # --- Tiling sub-graph (nodegroup_tiling) ---
    # Compute brick-texture-based tiling inline
    h_divide = nt.nodes.new("ShaderNodeMath")
    h_divide.operation = "DIVIDE"
    h_divide.inputs[0].default_value = 1.0
    h_divide.inputs[1].default_value = hscale

    mul_offset = nt.nodes.new("ShaderNodeMath")
    mul_offset.operation = "MULTIPLY"
    nt.links.new(h_divide.outputs[0], mul_offset.inputs[0])
    mul_offset.inputs[1].default_value = 1.0

    cxyz_offset = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(mul_offset.outputs[0], cxyz_offset.inputs["Y"])

    mapping_tile = nt.nodes.new("ShaderNodeMapping")
    mapping_tile.inputs["Location"].default_value = tuple(np.random.uniform(0, 1, 3))
    nt.links.new(tex_coord.outputs["Object"], mapping_tile.inputs["Vector"])

    vec_add = nt.nodes.new("ShaderNodeVectorMath")
    nt.links.new(mapping_tile.outputs["Vector"], vec_add.inputs[0])
    nt.links.new(cxyz_offset.outputs[0], vec_add.inputs[1])

    v_divide = nt.nodes.new("ShaderNodeMath")
    v_divide.operation = "DIVIDE"
    v_divide.inputs[0].default_value = 1.0
    v_divide.inputs[1].default_value = vscale

    brick = nt.nodes.new("ShaderNodeTexBrick")
    nt.links.new(vec_add.outputs["Vector"], brick.inputs["Vector"])
    brick.inputs["Color2"].default_value = (0, 0, 0, 1)
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Mortar Size"].default_value = 0.005
    brick.inputs["Mortar Smooth"].default_value = 1.0
    brick.inputs["Bias"].default_value = -0.5
    if "Brick Width" in brick.inputs:
        nt.links.new(v_divide.outputs[0], brick.inputs["Brick Width"])
    if "Row Height" in brick.inputs:
        nt.links.new(h_divide.outputs[0], brick.inputs["Row Height"])
    if hasattr(brick, "squash_frequency"):
        brick.squash_frequency = 1

    # tile_seed = brick_color * 1000 + seed_param
    mul_seed = nt.nodes.new("ShaderNodeMath")
    mul_seed.operation = "MULTIPLY_ADD"
    nt.links.new(brick.outputs["Color"], mul_seed.inputs[0])
    mul_seed.inputs[1].default_value = 1000.0
    mul_seed.inputs[2].default_value = seed_param

    # --- Wood grain sub-graph (nodegroup_tiled_wood) ---
    # Stretched mapping for musgrave-like grain
    mapping_grain = nt.nodes.new("ShaderNodeMapping")
    mapping_grain.inputs["Scale"].default_value = (5.0, 100.0, 100.0)
    nt.links.new(tex_coord.outputs["Object"], mapping_grain.inputs["Vector"])

    # musgrave_texture_2 substitute: 4D noise with grain mapping + tile seed
    musgrave_2 = nt.nodes.new("ShaderNodeTexNoise")
    _set_noise_dims(musgrave_2, "4D")
    nt.links.new(mapping_grain.outputs["Vector"], musgrave_2.inputs["Vector"])
    if "W" in musgrave_2.inputs:
        nt.links.new(mul_seed.outputs[0], musgrave_2.inputs["W"])
    musgrave_2.inputs["Scale"].default_value = 10.0
    if "Detail" in musgrave_2.inputs:
        musgrave_2.inputs["Detail"].default_value = 15.0

    mr_2 = nt.nodes.new("ShaderNodeMapRange")
    mr_2.inputs[3].default_value = 1.0
    mr_2.inputs[4].default_value = -1.0
    nt.links.new(_noise_fac_output(musgrave_2), mr_2.inputs[0])

    # mapping_1 (plain object coords)
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tex_coord.outputs["Object"], mapping_1.inputs["Vector"])

    # noise_texture_1: low-freq noise driven by tile seed
    noise_1 = nt.nodes.new("ShaderNodeTexNoise")
    _set_noise_dims(noise_1, "4D")
    nt.links.new(mapping_1.outputs["Vector"], noise_1.inputs["Vector"])
    if "W" in noise_1.inputs:
        nt.links.new(mul_seed.outputs[0], noise_1.inputs["W"])
    noise_1.inputs["Scale"].default_value = 0.5
    if "Detail" in noise_1.inputs:
        noise_1.inputs["Detail"].default_value = 1.0
    if "Distortion" in noise_1.inputs:
        noise_1.inputs["Distortion"].default_value = 1.1

    # musgrave_texture_1 substitute: noise driven by noise_1 fac + tile seed
    musgrave_1 = nt.nodes.new("ShaderNodeTexNoise")
    _set_noise_dims(musgrave_1, "4D")
    nt.links.new(_noise_fac_output(noise_1), musgrave_1.inputs["Vector"])
    if "W" in musgrave_1.inputs:
        nt.links.new(mul_seed.outputs[0], musgrave_1.inputs["W"])
    musgrave_1.inputs["Scale"].default_value = 0.5
    if "Detail" in musgrave_1.inputs:
        musgrave_1.inputs["Detail"].default_value = 15.0

    mr_1a = nt.nodes.new("ShaderNodeMapRange")
    mr_1a.inputs[3].default_value = -1.4
    mr_1a.inputs[4].default_value = 1.5
    nt.links.new(_noise_fac_output(musgrave_1), mr_1a.inputs[0])

    mr_1b = nt.nodes.new("ShaderNodeMapRange")
    mr_1b.inputs[3].default_value = 1.0
    mr_1b.inputs[4].default_value = 0.5
    nt.links.new(mr_1a.outputs["Result"], mr_1b.inputs[0])

    # mapping for radial grain
    mapping_radial = nt.nodes.new("ShaderNodeMapping")
    mapping_radial.inputs["Scale"].default_value = (0.15, 1.0, 0.15)
    nt.links.new(tex_coord.outputs["Object"], mapping_radial.inputs["Vector"])

    noise_radial = nt.nodes.new("ShaderNodeTexNoise")
    _set_noise_dims(noise_radial, "4D")
    nt.links.new(mapping_radial.outputs["Vector"], noise_radial.inputs["Vector"])
    if "W" in noise_radial.inputs:
        nt.links.new(mul_seed.outputs[0], noise_radial.inputs["W"])
    noise_radial.inputs["Scale"].default_value = 5.0
    if "Detail" in noise_radial.inputs:
        noise_radial.inputs["Detail"].default_value = 5.0
    if "Distortion" in noise_radial.inputs:
        noise_radial.inputs["Distortion"].default_value = 1.0

    # musgrave substitute for radial pattern
    musgrave_r = nt.nodes.new("ShaderNodeTexNoise")
    _set_noise_dims(musgrave_r, "4D")
    nt.links.new(_noise_fac_output(noise_radial), musgrave_r.inputs["Vector"])
    if "W" in musgrave_r.inputs:
        nt.links.new(mul_seed.outputs[0], musgrave_r.inputs["W"])
    musgrave_r.inputs["Scale"].default_value = 4.0
    if "Detail" in musgrave_r.inputs:
        musgrave_r.inputs["Detail"].default_value = 10.0

    # mix: noise_radial fac + musgrave_r
    mix_a = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_a, "data_type"):
        mix_a.data_type = "RGBA"
    mix_a.inputs[0].default_value = 0.5
    nt.links.new(_noise_fac_output(noise_radial), mix_a.inputs[6])
    nt.links.new(_noise_fac_output(musgrave_r), mix_a.inputs[7])

    # mix_1: MULTIPLY(mr_1b, mix_a)
    mix_b = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_b, "data_type"):
        mix_b.data_type = "RGBA"
    if hasattr(mix_b, "blend_type"):
        try:
            mix_b.blend_type = "MULTIPLY"
        except TypeError:
            pass
    mix_b.inputs[0].default_value = 0.9
    nt.links.new(mr_1b.outputs["Result"], mix_b.inputs[6])
    nt.links.new(mix_a.outputs[2], mix_b.inputs[7])

    # mix_2: MULTIPLY(mr_2, mix_b)
    mix_c = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_c, "data_type"):
        mix_c.data_type = "RGBA"
    if hasattr(mix_c, "blend_type"):
        try:
            mix_c.blend_type = "MULTIPLY"
        except TypeError:
            pass
    mix_c.inputs[0].default_value = 0.95
    nt.links.new(mr_2.outputs["Result"], mix_c.inputs[6])
    nt.links.new(mix_b.outputs[2], mix_c.inputs[7])

    # Hue/Sat/Value of base color
    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Saturation"].default_value = 0.8
    hsv_node.inputs["Value"].default_value = 0.2
    hsv_node.inputs["Fac"].default_value = 0.0
    hsv_node.inputs["Color"].default_value = base_color

    # mix_3: grain pattern mixes dark/light of base color
    mix_d = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_d, "data_type"):
        mix_d.data_type = "RGBA"
    nt.links.new(mix_c.outputs[2], mix_d.inputs[0])
    nt.links.new(hsv_node.outputs["Color"], mix_d.inputs[6])
    mix_d.inputs[7].default_value = base_color

    # mix_4: MULTIPLY with tile color to create tile boundaries
    mix_e = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_e, "data_type"):
        mix_e.data_type = "RGBA"
    if hasattr(mix_e, "blend_type"):
        try:
            mix_e.blend_type = "MULTIPLY"
        except TypeError:
            pass
    mix_e.inputs[0].default_value = 1.0
    nt.links.new(mix_d.outputs[2], mix_e.inputs[6])
    nt.links.new(brick.outputs["Color"], mix_e.inputs[7])

    # Roughness from float curve
    roughness_lo = float(np.random.uniform(0.3, 0.5))
    roughness_hi = float(np.random.uniform(0.8, 1.0))
    roughness_curve = _build_float_curve(nt, mix_e.outputs[2],
                                         [(0, roughness_lo), (1, roughness_hi)])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix_e.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(roughness_curve.outputs["Value"], bsdf.inputs["Roughness"])

    # Displacement: (brick_displacement + grain*0.1) * 0.01
    mul_grain_disp = nt.nodes.new("ShaderNodeMath")
    mul_grain_disp.operation = "MULTIPLY"
    nt.links.new(mix_c.outputs[2], mul_grain_disp.inputs[0])
    mul_grain_disp.inputs[1].default_value = 0.1

    add_disp = nt.nodes.new("ShaderNodeMath")
    nt.links.new(brick.outputs["Color"], add_disp.inputs[0])
    nt.links.new(mul_grain_disp.outputs[0], add_disp.inputs[1])

    mul_disp_final = nt.nodes.new("ShaderNodeMath")
    mul_disp_final.operation = "MULTIPLY"
    nt.links.new(add_disp.outputs[0], mul_disp_final.inputs[0])
    mul_disp_final.inputs[1].default_value = 0.01

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_disp_final.outputs[0], disp.inputs["Height"])

    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_wood(name="Wood", color=None):
    if color is None:
        bh, bs, bv = bark_hsv()
        color = hsv2rgba(
            bh + float(np.random.uniform(-0.0, 0.05)),
            bs + float(np.random.uniform(-0.3, 0.2)),
            bv * _mat_log_uniform(0.2, 20),
        )
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (5.0, 100.0, 100.0)
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    grain = nt.nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 10.0
    if "Detail" in grain.inputs:
        grain.inputs["Detail"].default_value = 15.0
    if "Distortion" in grain.inputs:
        grain.inputs["Distortion"].default_value = 0.5
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
    roughness_curve = _build_float_curve(
        nt, _noise_fac_output(noise_r),
        [(0, base_rough), (1, base_rough + float(np.random.uniform(0.0, 0.8)))])

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
    nt.links.new(roughness_curve.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_plastic_rough(name="PlasticRough", base_color=None):
    if base_color is None:
        base_color = hsv2rgba(float(np.random.uniform(0, 1)),
                              float(np.random.uniform(0.5, 0.8)),
                              _mat_log_uniform(0.01, 0.5))
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2000.0
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    roughness_input = float(np.random.uniform(0.0, 1.0))
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[0].default_value = roughness_input
    mr.inputs[3].default_value = 0.05
    mr.inputs[4].default_value = 0.25

    mul1 = nt.nodes.new("ShaderNodeMath")
    mul1.operation = "MULTIPLY"
    mul1.inputs[1].default_value = 0.4
    nt.links.new(mr.outputs["Result"], mul1.inputs[0])
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
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_glass_volume(name="GlassVolume"):
    if np.random.uniform(0, 1) < 0.3:
        color = (1, 1, 1, 1)
    else:
        color = hsv2rgba(float(np.random.uniform(0, 1)),
                         float(np.random.uniform(0.5, 0.9)),
                         float(np.random.uniform(0.6, 0.9)))
    density = 100.0

    mat = _new_material(name)
    nt = mat.node_tree

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=0.0, **{"Transmission Weight": 1.0})

    vol_absorb = nt.nodes.new("ShaderNodeVolumeAbsorption")
    vol_absorb.inputs["Color"].default_value = color
    vol_absorb.inputs["Density"].default_value = density

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    nt.links.new(vol_absorb.outputs[0], out.inputs["Volume"])
    return mat

# ----------------------------------------------------------------------------
# Material constructors: tableware registry
# ----------------------------------------------------------------------------

def make_ceramic(name="Ceramic"):
    if np.random.uniform(0, 1) < 0.8:
        color = hsv2rgba(float(np.random.uniform(0, 1)),
                         float(np.random.uniform(0.2, 0.4)),
                         _mat_log_uniform(0.3, 0.6))
    else:
        color = hsv2rgba(0.0, 0.0, _mat_log_uniform(0.3, 0.6))

    roughness_min = 0.0
    roughness_max = 0.8

    mat = _new_material(name)
    nt = mat.node_tree

    def _musgrave_curve(scale_range):
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = _mat_log_uniform(*scale_range)
        if "Detail" in noise.inputs:
            noise.inputs["Detail"].default_value = 15.0
        return _build_float_curve(
            nt, _noise_fac_output(noise),
            [(0.0, roughness_min), (1.0, roughness_max)])

    roughness_curve = _musgrave_curve((20, 40))
    coat_rough_curve = _musgrave_curve((20, 40))

    disp_noise = nt.nodes.new("ShaderNodeTexNoise")
    disp_noise.inputs["Scale"].default_value = _mat_log_uniform(20, 40)
    mul_disp = nt.nodes.new("ShaderNodeMath")
    mul_disp.operation = "MULTIPLY"
    mul_disp.inputs[1].default_value = _mat_log_uniform(0.001, 0.005)
    nt.links.new(_noise_fac_output(disp_noise), mul_disp.inputs[0])
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_disp.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
    nt.links.new(roughness_curve.outputs["Value"], bsdf.inputs["Roughness"])
    _set_principled(bsdf, **{
        "Coat Weight": 1.0,
        "Specular IOR Level": 1.0,
        "Subsurface Weight": float(np.random.uniform(0.02, 0.05)),
    })
    if "Coat Roughness" in bsdf.inputs:
        nt.links.new(coat_rough_curve.outputs["Value"], bsdf.inputs["Coat Roughness"])
    elif "Clearcoat Roughness" in bsdf.inputs:
        nt.links.new(coat_rough_curve.outputs["Value"],
                     bsdf.inputs["Clearcoat Roughness"])

    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_glass(name="Glass"):
    if np.random.uniform(0, 1) < 0.5:
        color = (1, 1, 1, 1)
    else:
        color = hsv2rgba(float(np.random.uniform(0, 1)),
                         float(np.random.uniform(0.05, 0.25)),
                         1.0)

    mat = _new_material(name)
    nt = mat.node_tree

    glass_bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    glass_bsdf.inputs["Roughness"].default_value = 0.02
    glass_bsdf.inputs["IOR"].default_value = 1.5
    if "Transmission Weight" in glass_bsdf.inputs:
        glass_bsdf.inputs["Transmission Weight"].default_value = 1.0
    elif "Transmission" in glass_bsdf.inputs:
        glass_bsdf.inputs["Transmission"].default_value = 1.0

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(glass_bsdf.outputs[0], out.inputs["Surface"])
    return mat

def make_plastic(name="Plastic"):
    """Chooses between rough and translucent based on random draws, mirroring
    Plastic.sample_plastic().
    """

    is_rough = float(np.random.uniform(0, 1))
    is_translucent = float(np.random.uniform(0, 1))
    clear = np.random.uniform() < 0.2

    if is_rough > is_translucent:
        # plastic_rough path
        if clear:
            base_color = hsv2rgba(0.0, 0.0, _mat_log_uniform(0.4, 0.8))
        else:
            base_color = hsv2rgba(float(np.random.uniform(0, 1)),
                                  float(np.random.uniform(0.5, 0.8)),
                                  _mat_log_uniform(0.01, 0.5))
        return make_plastic_rough(name=name, base_color=base_color)
    else:
        # plastic_translucent path
        mat = _new_material(name)
        nt = mat.node_tree

        blend_val = float(random.random() * 0.2 + 0.2)  # sample_range(0.2, 0.4)
        layer_weight = nt.nodes.new("ShaderNodeLayerWeight")
        layer_weight.inputs["Blend"].default_value = blend_val

        if clear:
            base_color = hsv2rgba(0, 0, _mat_log_uniform(0.4, 0.8))
        else:
            base_color = hsv2rgba(float(np.random.uniform(0, 1)),
                                  float(np.random.uniform(0.5, 0.8)),
                                  _mat_log_uniform(0.4, 0.8))

        ior_val = float(random.random() * 0.4 + 1.2)  # sample_range(1.2, 1.6)

        glass_bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        glass_bsdf.inputs["Base Color"].default_value = base_color
        glass_bsdf.inputs["Roughness"].default_value = 0.2
        glass_bsdf.inputs["IOR"].default_value = ior_val
        if "Transmission Weight" in glass_bsdf.inputs:
            glass_bsdf.inputs["Transmission Weight"].default_value = 1.0
        elif "Transmission" in glass_bsdf.inputs:
            glass_bsdf.inputs["Transmission"].default_value = 1.0

        glossy_bsdf = nt.nodes.new("ShaderNodeBsdfGlossy")
        glossy_bsdf.inputs["Roughness"].default_value = 0.2

        mix_shader = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(layer_weight.outputs["Fresnel"], mix_shader.inputs["Fac"])
        nt.links.new(glass_bsdf.outputs[0], mix_shader.inputs[1])
        nt.links.new(glossy_bsdf.outputs[0], mix_shader.inputs[2])

        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(mix_shader.outputs[0], out.inputs["Surface"])
        return mat

def make_metal_basic(name="MetalBasic", color_hsv=None):
    color_hsv = color_hsv or metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(np.random.uniform(10, 25))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    roughness_lo = float(np.random.uniform(0, 0.2))
    roughness_hi = float(np.random.uniform(0.4, 0.7))
    roughness_curve = _build_float_curve(
        nt, _noise_fac_output(noise),
        [(0, roughness_lo), (1, roughness_hi)])

    spec_ior = float(np.random.uniform(0.5, 1.0))
    base_color_rgba = hsv2rgba(*color_hsv)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Metallic=1.0, **{
        "Specular IOR Level": spec_ior,
        "Base Color": base_color_rgba,
    })
    nt.links.new(roughness_curve.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

# ----------------------------------------------------------------------------
# Registries -- mirror material_assignments.py entries
# ----------------------------------------------------------------------------

# material_assignments.py:191-197 -- table_top (second definition, active)
TABLE_TOP = [
    (make_marble, 1.0),
    (make_tiled_wood, 1.0),
    (make_wood, 1.0),
    (make_plastic_rough, 0.5),
    (make_glass_volume, 1.0),
]

# material_assignments.py:199-205 -- tableware
TABLEWARE = [
    (make_ceramic, 1.0),
    (make_glass, 1.0),
    (make_plastic, 1.0),
    (make_metal_basic, 1.0),
    (make_wood, 1.0),
]

REGISTRY = {
    "table_top": TABLE_TOP,
    "tableware": TABLEWARE,
}

def get_material(registry_key, name=None):
    ctor = weighted_sample_mat(REGISTRY[registry_key])
    return ctor(name=name or registry_key.title())

# --- Seed (will be overridden by Phase 1) ---
SEED = int(os.environ.get('SEED', 0))
random.seed(SEED)
np.random.seed(SEED)

# --- Scene cleanup ---
for _obj in list(bpy.data.objects):
    bpy.data.objects.remove(_obj, do_unlink=True)
for _m in list(bpy.data.meshes):
    bpy.data.meshes.remove(_m)
for _ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(_ng)
bpy.context.scene.cursor.location = (0, 0, 0)

# FixedSeed(factory_seed)). Material sampling order follows
# TableDiningFactory.get_material_params (dining_table.py:210-222):
#   1. TopMaterial = weighted_sample(table_top)()
#   2. LegMaterial = weighted_sample(tableware)()
#   3. scratch probability gate (consumed but NOT applied)
#   4. edge_wear probability gate (consumed but NOT applied)
#
# dining_table.py finalize_assets (line 333) is `pass` -> no wear_tear applied.
seed_all(SEED)
MAT_TOP = get_material("table_top", "TableTop")
MAT_LEG = get_material("tableware", "TableLeg")
# Consume RNG for wear_tear probability gates (alignment only, not applied)
_scratch_gate = np.random.uniform()    # noqa: F841  -- consumed for alignment
_edge_wear_gate = np.random.uniform()  # noqa: F841  -- consumed for alignment

# --- Original geometry code (copied verbatim from objects_blender/tables/
#     CoffeeTableFactory.py), with SetMaterial nodes inserted in the
#     assembly GeoNodes before the final join. ================================

def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

# socket type shorthand
_STY = {
    "F": "NodeSocketFloat", "I": "NodeSocketInt", "B": "NodeSocketBool",
    "V": "NodeSocketVector", "G": "NodeSocketGeometry",
}

def NG(name, ins=(), outs=()):
    """Create a new GeometryNodeTree with interface sockets."""

    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    for spec in ins:
        nm, ty = spec[0], spec[1]
        s = ng.interface.new_socket(nm, in_out="INPUT", socket_type=_STY[ty])
        if len(spec) > 2 and hasattr(s, "default_value"):
            try:
                s.default_value = spec[2]
            except Exception:
                pass
    for spec in outs:
        nm, ty = spec[0], spec[1]
        ng.interface.new_socket(nm, in_out="OUTPUT", socket_type=_STY[ty])
    return ng

def IO(ng):
    gi = ng.nodes.new("NodeGroupInput")
    go = ng.nodes.new("NodeGroupOutput")
    return gi, go

def _wire(ng, sock, val):
    if isinstance(val, bpy.types.NodeSocket):
        ng.links.new(val, sock)
        return
    if isinstance(val, tuple) and len(val) == 2 and isinstance(val[0], bpy.types.Node):
        node, key = val
        out = node.outputs[key]
        ng.links.new(out, sock)
        return
    if isinstance(val, bpy.types.Node):
        ng.links.new(val.outputs[0], sock)
        return
    try:
        sock.default_value = val
    except Exception:
        pass

def N(ng, node_type, ins=None, attrs=None):
    n = ng.nodes.new(node_type)
    if attrs:
        for k, v in attrs.items():
            try:
                setattr(n, k, v)
            except Exception:
                pass
    if ins:
        for k, v in ins.items():
            try:
                sock = n.inputs[k]
            except Exception:
                continue
            _wire(ng, sock, v)
    return n

def L(ng, a, b):
    if isinstance(a, bpy.types.Node):
        a = a.outputs[0]
    ng.links.new(a, b)

# Blender 5.0 compat helpers
def set_fillet_mode(node, mode):
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

def assign_float_curve(mapping, ctrl_pts):
    curve = mapping.curves[0]
    while len(curve.points) > 2:
        curve.points.remove(curve.points[-1])
    for i, (x, y) in enumerate(ctrl_pts):
        if i < len(curve.points):
            curve.points[i].location = (x, y)
        else:
            curve.points.new(x, y)
    for pt in curve.points:
        pt.handle_type = "AUTO"
    mapping.update()

# shorthand node-type strings used repeatedly
_CXYZ = "ShaderNodeCombineXYZ"
_MATH = "ShaderNodeMath"
_VMATH = "ShaderNodeVectorMath"
_XFORM = "GeometryNodeTransform"
_GRP = "GeometryNodeGroup"

def cxyz(ng, x=None, y=None, z=None):
    ins = {}
    if x is not None: ins["X"] = x
    if y is not None: ins["Y"] = y
    if z is not None: ins["Z"] = z
    return N(ng, _CXYZ, ins=ins)

def math_op(ng, op, a, b=None):
    ins = {0: a}
    if b is not None:
        ins[1] = b
    return N(ng, _MATH, ins=ins, attrs={"operation": op})

def vmath_op(ng, op, a, b=None):
    ins = {0: a}
    if b is not None:
        ins[1] = b
    return N(ng, _VMATH, ins=ins, attrs={"operation": op})

def xform(ng, geo, translation=None, rotation=None, scale=None):
    ins = {"Geometry": geo}
    if translation is not None: ins["Translation"] = translation
    if rotation is not None: ins["Rotation"] = rotation
    if scale is not None: ins["Scale"] = scale
    return N(ng, _XFORM, ins=ins)

def grp(ng, name, ins=None):
    node = ng.nodes.new(_GRP)
    node.node_tree = bpy.data.node_groups[name]
    if ins:
        for k, v in ins.items():
            try:
                _wire(ng, node.inputs[k], v)
            except Exception:
                continue
    return node

# -- GeoNodes builders -------------------------------------------------------

def build_n_gon_profile():
    ng = NG("n_gon_profile",
        ins=[("Profile N-gon", "I", 4), ("Profile Width", "F", 1.0),
             ("Profile Aspect Ratio", "F", 1.0), ("Profile Fillet Ratio", "F", 0.2)],
        outs=[("Output", "G")])
    gi, go = IO(ng)

    val = N(ng, "ShaderNodeValue")
    val.outputs[0].default_value = 0.5

    cc = N(ng, "GeometryNodeCurvePrimitiveCircle",
           ins={"Resolution": (gi, "Profile N-gon"), "Radius": val},
           attrs={"mode": "RADIUS"})

    div = math_op(ng, "DIVIDE", math.pi, (gi, "Profile N-gon"))
    t1 = xform(ng, (cc, "Curve"), rotation=cxyz(ng, z=div))
    t2 = xform(ng, t1, rotation=(0, 0, -math.pi / 2))

    mul_ar = math_op(ng, "MULTIPLY", (gi, "Profile Aspect Ratio"), (gi, "Profile Width"))
    cxy = cxyz(ng, x=(gi, "Profile Width"), y=mul_ar, z=1.0)

    t3 = xform(ng, t2, scale=cxy)

    mul_f = math_op(ng, "MULTIPLY", (gi, "Profile Width"), (gi, "Profile Fillet Ratio"))
    fc = N(ng, "GeometryNodeFilletCurve",
           ins={"Curve": t3, "Count": 8, "Radius": mul_f, "Limit Radius": True})
    set_fillet_mode(fc, "POLY")

    L(ng, fc.outputs[0], go.inputs["Output"])
    return ng

def build_n_gon_cylinder():
    ng = NG("n_gon_cylinder",
        ins=[("Radius Curve", "G"), ("Height", "F", 0.5), ("N-gon", "I"),
             ("Profile Width", "F", 0.5), ("Aspect Ratio", "F", 0.5),
             ("Fillet Ratio", "F", 0.2), ("Profile Resolution", "I", 64),
             ("Resolution", "I", 128)],
        outs=[("Mesh", "G"), ("Profile Curve", "G"), ("Caps", "G")])
    gi, go = IO(ng)

    mul_h = math_op(ng, "MULTIPLY", (gi, "Height"), -1.0)
    cz_h = cxyz(ng, z=mul_h)

    cl = N(ng, "GeometryNodeCurvePrimitiveLine", ins={"End": cz_h})
    tilt = N(ng, "GeometryNodeSetCurveTilt", ins={"Curve": cl, "Tilt": math.pi})
    rs = N(ng, "GeometryNodeResampleCurve",
           ins={"Curve": tilt, "Count": (gi, "Resolution")})

    sp = N(ng, "GeometryNodeSplineParameter")

    cap = N(ng, "GeometryNodeCaptureAttribute", ins={"Geometry": rs})
    set_capture_data_type(cap, "FLOAT")
    val_input = None
    for inp in cap.inputs:
        if inp.name == "Value" and inp.bl_idname != "NodeSocketGeometry":
            val_input = inp
            break
    if val_input is None:
        val_input = cap.inputs[1]
    L(ng, sp.outputs["Factor"], val_input)

    ngp = grp(ng, "n_gon_profile", ins={
        "Profile N-gon": (gi, "N-gon"),
        "Profile Width": (gi, "Profile Width"),
        "Profile Aspect Ratio": (gi, "Aspect Ratio"),
        "Profile Fillet Ratio": (gi, "Fillet Ratio"),
    })
    rs2 = N(ng, "GeometryNodeResampleCurve",
            ins={"Curve": ngp, "Count": (gi, "Profile Resolution")})

    cap_geo_out = cap.outputs["Geometry"] if "Geometry" in cap.outputs else cap.outputs[0]
    c2m = N(ng, "GeometryNodeCurveToMesh",
            ins={"Curve": cap_geo_out, "Profile Curve": rs2, "Fill Caps": True})

    cap_attr_out = None
    for o in cap.outputs:
        if o.name == "Value" and o.bl_idname != "NodeSocketGeometry":
            cap_attr_out = o
            break
    if cap_attr_out is None:
        cap_attr_out = cap.outputs[1]

    pos1 = N(ng, "GeometryNodeInputPosition")
    sep1 = N(ng, "ShaderNodeSeparateXYZ", ins={0: pos1})

    sc = N(ng, "GeometryNodeSampleCurve",
           ins={"Curves": (gi, "Radius Curve"), "Factor": cap_attr_out})
    try:
        sc.use_all_curves = True
    except AttributeError:
        pass

    sep2 = N(ng, "ShaderNodeSeparateXYZ", ins={0: (sc, "Position")})
    cxy_xy = cxyz(ng, x=(sep2, "X"), y=(sep2, "Y"))
    length = vmath_op(ng, "LENGTH", cxy_xy)

    mulx = math_op(ng, "MULTIPLY", (sep1, "X"), (length, "Value"))
    muly = math_op(ng, "MULTIPLY", (sep1, "Y"), (length, "Value"))

    pos2 = N(ng, "GeometryNodeInputPosition")
    sep3 = N(ng, "ShaderNodeSeparateXYZ", ins={0: pos2})

    as_node = N(ng, "GeometryNodeAttributeStatistic",
                ins={"Geometry": (gi, "Radius Curve")}, attrs={"data_type": "FLOAT"})
    as_attr_input = None
    for inp in as_node.inputs:
        if inp.name == "Attribute" and inp.bl_idname == "NodeSocketFloat":
            as_attr_input = inp
            break
    if as_attr_input is None:
        as_attr_input = as_node.inputs[2]
    L(ng, sep3.outputs["Z"], as_attr_input)

    mr = N(ng, "ShaderNodeMapRange",
           ins={"Value": (sep2, "Z"), 1: (as_node, "Min"), 2: (as_node, "Max"),
                3: mul_h, 4: 0.0})

    cfinal = cxyz(ng, x=mulx, y=muly, z=(mr, "Result"))
    sp2 = N(ng, "GeometryNodeSetPosition",
            ins={"Geometry": c2m, "Position": cfinal})

    idx = N(ng, "GeometryNodeInputIndex")
    ds = N(ng, "GeometryNodeAttributeDomainSize", ins={0: c2m})
    sub = math_op(ng, "SUBTRACT", (ds, "Face Count"), 2.0)

    lt = N(ng, "FunctionNodeCompare", ins={2: idx, 3: sub},
           attrs={"data_type": "INT", "operation": "LESS_THAN"})
    delg = N(ng, "GeometryNodeDeleteGeometry",
             ins={"Geometry": c2m, "Selection": lt}, attrs={"domain": "FACE"})

    L(ng, sp2.outputs[0], go.inputs["Mesh"])
    L(ng, rs2.outputs[0], go.inputs["Profile Curve"])
    L(ng, delg.outputs[0], go.inputs["Caps"])
    return ng

def build_generate_radius_curve(ctrl_pts):
    name = f"generate_radius_curve_{id(ctrl_pts)}"
    ng = NG(name,
        ins=[("Resolution", "I", 128)],
        outs=[("Geometry", "G")])
    gi, go = IO(ng)

    cl = N(ng, "GeometryNodeCurvePrimitiveLine",
           ins={"Start": (1.0, 0.0, 1.0), "End": (1.0, 0.0, -1.0)})
    rs = N(ng, "GeometryNodeResampleCurve",
           ins={"Curve": cl, "Count": (gi, "Resolution")})

    pos = N(ng, "GeometryNodeInputPosition")
    sp = N(ng, "GeometryNodeSplineParameter")
    fc = N(ng, "ShaderNodeFloatCurve", ins={"Value": (sp, "Factor")})
    assign_float_curve(fc.mapping, ctrl_pts)

    cxy = cxyz(ng, x=fc, y=1.0, z=1.0)
    mul = vmath_op(ng, "MULTIPLY", pos, cxy)

    sp2 = N(ng, "GeometryNodeSetPosition",
            ins={"Geometry": rs, "Position": (mul, "Vector")})
    L(ng, sp2.outputs[0], go.inputs["Geometry"])
    return ng

def build_create_anchors():
    ng = NG("create_anchors",
        ins=[("Profile N-gon", "I"), ("Profile Width", "F", 0.5),
             ("Profile Aspect Ratio", "F", 0.5), ("Profile Rotation", "F")],
        outs=[("Geometry", "G")])
    gi, go = IO(ng)

    eq1 = N(ng, "FunctionNodeCompare", ins={2: (gi, "Profile N-gon"), 3: 1},
            attrs={"data_type": "INT", "operation": "EQUAL"})
    eq2 = N(ng, "FunctionNodeCompare", ins={2: (gi, "Profile N-gon"), 3: 2},
            attrs={"data_type": "INT", "operation": "EQUAL"})

    ngp = grp(ng, "n_gon_profile", ins={
        "Profile N-gon": (gi, "Profile N-gon"),
        "Profile Width": (gi, "Profile Width"),
        "Profile Aspect Ratio": (gi, "Profile Aspect Ratio"),
        "Profile Fillet Ratio": 0.0,
    })
    c2p = N(ng, "GeometryNodeCurveToPoints", ins={"Curve": ngp}, attrs={"mode": "EVALUATED"})

    mul_pos = math_op(ng, "MULTIPLY", (gi, "Profile Width"), 0.3535)
    mul_neg = math_op(ng, "MULTIPLY", (gi, "Profile Width"), -0.3535)
    cxp = cxyz(ng, x=mul_pos)
    cxn = cxyz(ng, x=mul_neg)
    cl2 = N(ng, "GeometryNodeCurvePrimitiveLine", ins={"Start": cxp, "End": cxn})
    c2p2 = N(ng, "GeometryNodeCurveToPoints", ins={"Curve": cl2}, attrs={"mode": "EVALUATED"})

    sw1 = N(ng, "GeometryNodeSwitch", attrs={"input_type": "GEOMETRY"},
            ins={0: eq2, 1: (c2p, "Points"), 2: (c2p2, "Points")})

    pts = N(ng, "GeometryNodePoints")
    sw2 = N(ng, "GeometryNodeSwitch", attrs={"input_type": "GEOMETRY"},
            ins={0: eq1, 1: sw1, 2: pts})

    spr = N(ng, "GeometryNodeSetPointRadius", ins={"Points": sw2})
    cz_rot = cxyz(ng, z=(gi, "Profile Rotation"))
    tf = xform(ng, spr, rotation=cz_rot)
    L(ng, tf.outputs[0], go.inputs["Geometry"])
    return ng

def build_create_legs_and_strechers():
    ng = NG("create_legs_and_strechers",
        ins=[("Anchors", "G"), ("Keep Legs", "B"), ("Leg Instance", "G"),
             ("Table Height", "F"), ("Leg Bottom Relative Scale", "F"),
             ("Leg Bottom Relative Rotation", "F"),
             ("Keep Odd Strechers", "B", True), ("Keep Even Strechers", "B", True),
             ("Strecher Instance", "G"), ("Strecher Index Increment", "I"),
             ("Strecher Relative Position", "F", 0.5), ("Leg Bottom Offset", "F"),
             ("Align Leg X rot", "B")],
        outs=[("Geometry", "G")])
    gi, go = IO(ng)

    cz_th = cxyz(ng, z=(gi, "Table Height"))
    tf_anch = xform(ng, (gi, "Anchors"), translation=cz_th)

    pos = N(ng, "GeometryNodeInputPosition")
    cz_off = cxyz(ng, z=(gi, "Leg Bottom Offset"))
    sub1 = vmath_op(ng, "SUBTRACT", cz_th, cz_off)
    sub2 = vmath_op(ng, "SUBTRACT", pos, (sub1, "Vector"))

    vr = N(ng, "ShaderNodeVectorRotate",
           ins={"Vector": (sub2, "Vector"), "Angle": (gi, "Leg Bottom Relative Rotation")},
           attrs={"rotation_type": "Z_AXIS"})

    cxyz_bs = cxyz(ng, x=(gi, "Leg Bottom Relative Scale"),
                   y=(gi, "Leg Bottom Relative Scale"), z=1.0)
    mul_bs = vmath_op(ng, "MULTIPLY", vr, cxyz_bs)
    sub3 = vmath_op(ng, "SUBTRACT", pos, (mul_bs, "Vector"))

    ae1 = N(ng, "FunctionNodeAlignEulerToVector",
            ins={"Vector": (sub3, "Vector")}, attrs={"axis": "Z"})
    ae2 = N(ng, "FunctionNodeAlignEulerToVector",
            ins={"Rotation": ae1, "Vector": pos}, attrs={"pivot_axis": "Z"})
    sw_align = N(ng, "GeometryNodeSwitch", attrs={"input_type": "VECTOR"},
                 ins={0: (gi, "Align Leg X rot"), 1: ae1, 2: ae2})

    len_leg = vmath_op(ng, "LENGTH", (sub3, "Vector"))
    cxyz_sc = cxyz(ng, x=1.0, y=1.0, z=(len_leg, "Value"))

    iop = N(ng, "GeometryNodeInstanceOnPoints",
            ins={"Points": tf_anch, "Instance": (gi, "Leg Instance"),
                 "Rotation": sw_align, "Scale": cxyz_sc})
    real = N(ng, "GeometryNodeRealizeInstances", ins={0: iop})

    sw_leg = N(ng, "GeometryNodeSwitch", attrs={"input_type": "GEOMETRY"},
               ins={0: (gi, "Keep Legs"), 2: real})

    # stretchers
    mul_srp = math_op(ng, "MULTIPLY", (gi, "Strecher Relative Position"), -1.0)
    sc_vec = N(ng, "ShaderNodeVectorMath",
               ins={0: (sub3, "Vector"), "Scale": mul_srp},
               attrs={"operation": "SCALE"})

    pos2 = N(ng, "GeometryNodeInputPosition")
    add_sp = N(ng, "ShaderNodeVectorMath", ins={0: (sc_vec, "Vector"), 1: pos2})

    setp = N(ng, "GeometryNodeSetPosition",
             ins={"Geometry": tf_anch, "Position": (add_sp, "Vector")})

    idx = N(ng, "GeometryNodeInputIndex")
    mod = math_op(ng, "MODULO", idx, 2.0)
    and_odd = N(ng, "FunctionNodeBooleanMath",
                ins={0: mod, 1: (gi, "Keep Odd Strechers")})
    not_mod = N(ng, "FunctionNodeBooleanMath", ins={0: mod}, attrs={"operation": "NOT"})
    and_even = N(ng, "FunctionNodeBooleanMath",
                 ins={0: (gi, "Keep Even Strechers"), 1: not_mod})
    or_oe = N(ng, "FunctionNodeBooleanMath",
              ins={0: and_odd, 1: and_even}, attrs={"operation": "OR"})

    ds = N(ng, "GeometryNodeAttributeDomainSize", ins={0: tf_anch},
           attrs={"component": "POINTCLOUD"})
    div_si = math_op(ng, "DIVIDE", (ds, "Point Count"), (gi, "Strecher Index Increment"))
    eq2_node = N(ng, "FunctionNodeCompare", ins={0: div_si, 1: 2.0}, attrs={"operation": "EQUAL"})

    bool_true = N(ng, "FunctionNodeInputBool")
    bool_true.boolean = True
    idx2 = N(ng, "GeometryNodeInputIndex")
    div2 = math_op(ng, "DIVIDE", (ds, "Point Count"), 2.0)
    lt_half = N(ng, "FunctionNodeCompare", ins={2: idx2, 3: div2},
                attrs={"data_type": "INT", "operation": "LESS_THAN"})
    sw_half = N(ng, "GeometryNodeSwitch", attrs={"input_type": "BOOLEAN"},
                ins={0: eq2_node, 1: bool_true, 2: lt_half})
    and_final = N(ng, "FunctionNodeBooleanMath", ins={0: or_oe, 1: sw_half})

    pos3 = N(ng, "GeometryNodeInputPosition")
    add_inc = N(ng, "ShaderNodeMath", ins={0: idx, 1: (gi, "Strecher Index Increment")})
    mod_wrap = math_op(ng, "MODULO", add_inc, (ds, "Point Count"))
    fai = N(ng, "GeometryNodeFieldAtIndex",
            ins={"Index": mod_wrap, 1: pos3}, attrs={"data_type": "FLOAT_VECTOR"})
    sub_dir = vmath_op(ng, "SUBTRACT", pos3, fai)

    ae_s1 = N(ng, "FunctionNodeAlignEulerToVector",
              ins={"Vector": (sub_dir, "Vector")}, attrs={"axis": "Z"})
    ae_s2 = N(ng, "FunctionNodeAlignEulerToVector",
              ins={"Rotation": ae_s1}, attrs={"pivot_axis": "Z"})
    len_s = vmath_op(ng, "LENGTH", (sub_dir, "Vector"))
    cxyz_ss = cxyz(ng, x=1.0, y=1.0, z=(len_s, "Value"))

    iop_s = N(ng, "GeometryNodeInstanceOnPoints",
              ins={"Points": setp, "Selection": and_final,
                   "Instance": (gi, "Strecher Instance"),
                   "Rotation": ae_s2, "Scale": cxyz_ss})
    real_s = N(ng, "GeometryNodeRealizeInstances", ins={0: iop_s})

    join = N(ng, "GeometryNodeJoinGeometry")
    L(ng, sw_leg.outputs[0], join.inputs["Geometry"])
    L(ng, real_s.outputs[0], join.inputs["Geometry"])
    L(ng, join.outputs[0], go.inputs["Geometry"])
    return ng

def build_generate_table_top():
    ng = NG("generate_table_top",
        ins=[("Thickness", "F", 0.5), ("N-gon", "I"),
             ("Profile Width", "F", 0.5), ("Aspect Ratio", "F", 0.5),
             ("Fillet Ratio", "F", 0.2), ("Fillet Radius Vertical", "F")],
        outs=[("Geometry", "G"), ("Curve", "G")])
    gi, go = IO(ng)

    cl = N(ng, "GeometryNodeCurvePrimitiveLine",
           ins={"Start": (1.0, 0.0, 1.0), "End": (1.0, 0.0, -1.0)})
    ngc = grp(ng, "n_gon_cylinder", ins={
        "Radius Curve": cl,
        "Height": (gi, "Thickness"),
        "N-gon": (gi, "N-gon"),
        "Profile Width": (gi, "Profile Width"),
        "Aspect Ratio": (gi, "Aspect Ratio"),
        "Fillet Ratio": (gi, "Fillet Ratio"),
        "Profile Resolution": 512,
        "Resolution": 10,
    })

    arc = N(ng, "GeometryNodeCurveArc",
            ins={"Resolution": 4, "Radius": 0.7071, "Sweep Angle": 4.7124})
    t1 = xform(ng, (arc, "Curve"), rotation=(0, 0, -0.7854))
    t2 = xform(ng, t1, rotation=(0, math.pi / 2, 0))
    t3 = xform(ng, t2, translation=(0, 0.5, 0))

    cxyz_fr = cxyz(ng, x=1.0, y=(gi, "Fillet Radius Vertical"), z=1.0)
    t4 = xform(ng, t3, scale=cxyz_fr)

    fc = N(ng, "GeometryNodeFilletCurve",
           ins={"Curve": t4, "Count": 8,
                "Radius": (gi, "Fillet Radius Vertical"), "Limit Radius": True})
    set_fillet_mode(fc, "POLY")

    t5 = N(ng, "GeometryNodeTransform",
           ins={"Geometry": fc, "Rotation": (math.pi / 2, math.pi / 2, 0),
                "Scale": (gi, "Thickness")})

    c2m = N(ng, "GeometryNodeCurveToMesh",
            ins={"Curve": (ngc, "Profile Curve"), "Profile Curve": t5})

    mul_th = math_op(ng, "MULTIPLY", (gi, "Thickness"), -0.5)
    cz_th = cxyz(ng, z=mul_th)
    t6 = xform(ng, c2m, translation=cz_th)

    join = N(ng, "GeometryNodeJoinGeometry")
    L(ng, t6.outputs[0], join.inputs["Geometry"])
    L(ng, ngc.outputs["Caps"], join.inputs["Geometry"])

    flip = N(ng, "GeometryNodeFlipFaces", ins={"Mesh": join})
    cz_up = cxyz(ng, z=(gi, "Thickness"))
    t7 = xform(ng, flip, translation=cz_up)

    L(ng, t7.outputs[0], go.inputs["Geometry"])
    L(ng, ngc.outputs["Profile Curve"], go.inputs["Curve"])
    return ng

def build_generate_leg_straight(ctrl_pts):
    rc_ng = build_generate_radius_curve(ctrl_pts)
    ng = NG("generate_leg_straight",
        ins=[("Leg Height", "F"), ("Leg Diameter", "F", 1.0),
             ("Resolution", "I"), ("N-gon", "I", 32), ("Fillet Ratio", "F", 0.01)],
        outs=[("Geometry", "G")])
    gi, go = IO(ng)

    rc = N(ng, _GRP)
    rc.node_tree = rc_ng
    L(ng, gi.outputs["Resolution"], rc.inputs["Resolution"])

    ngc = grp(ng, "n_gon_cylinder", ins={
        "Radius Curve": rc,
        "Height": (gi, "Leg Height"),
        "N-gon": (gi, "N-gon"),
        "Profile Width": (gi, "Leg Diameter"),
        "Aspect Ratio": 1.0,
        "Fillet Ratio": (gi, "Fillet Ratio"),
        "Resolution": (gi, "Resolution"),
    })
    L(ng, ngc.outputs["Mesh"], go.inputs["Geometry"])
    return ng

def build_generate_single_stand(ctrl_pts):
    rc_ng = build_generate_radius_curve(ctrl_pts)
    ng = NG("generate_single_stand",
        ins=[("Leg Height", "F"), ("Leg Diameter", "F", 1.0), ("Resolution", "I", 64)],
        outs=[("Geometry", "G")])
    gi, go = IO(ng)

    rc = N(ng, _GRP)
    rc.node_tree = rc_ng
    L(ng, gi.outputs["Resolution"], rc.inputs["Resolution"])

    ngc = grp(ng, "n_gon_cylinder", ins={
        "Radius Curve": rc,
        "Height": (gi, "Leg Height"),
        "N-gon": (gi, "Resolution"),
        "Profile Width": (gi, "Leg Diameter"),
        "Aspect Ratio": 1.0,
        "Fillet Ratio": 0.0,
        "Resolution": (gi, "Resolution"),
    })
    L(ng, ngc.outputs["Mesh"], go.inputs["Geometry"])
    return ng

def build_merge_curve():
    ng = NG("merge_curve", ins=[("Curve", "G")], outs=[("Curve", "G")])
    gi, go = IO(ng)
    c2m = N(ng, "GeometryNodeCurveToMesh", ins={"Curve": (gi, "Curve")})
    mbd = N(ng, "GeometryNodeMergeByDistance", ins={"Geometry": c2m})
    m2c = N(ng, "GeometryNodeMeshToCurve", ins={"Mesh": mbd})
    L(ng, m2c.outputs[0], go.inputs["Curve"])
    return ng

def build_generate_leg_square():
    ng = NG("generate_leg_square",
        ins=[("Width", "F"), ("Height", "F"), ("Fillet Radius", "F", 0.03),
             ("Has Bottom Connector", "B", True), ("Profile N-gon", "I", 4),
             ("Profile Width", "F", 0.1), ("Profile Aspect Ratio", "F", 0.5),
             ("Profile Fillet Ratio", "F", 0.1)],
        outs=[("Geometry", "G")])
    gi, go = IO(ng)

    add_node = N(ng, "ShaderNodeMath", ins={0: (gi, "Has Bottom Connector"), 1: 4.0})
    mr1 = N(ng, "ShaderNodeMapRange",
            ins={"Value": (gi, "Has Bottom Connector"), 3: 4.7124, 4: 6.2832})
    arc = N(ng, "GeometryNodeCurveArc",
            ins={"Resolution": add_node, "Radius": 0.7071, "Sweep Angle": (mr1, "Result")})

    mc = grp(ng, "merge_curve", ins={"Curve": (arc, "Curve")})

    mr2 = N(ng, "ShaderNodeMapRange",
            ins={"Value": (gi, "Has Bottom Connector"), 3: 1.5708, 4: 3.1416})
    sct = N(ng, "GeometryNodeSetCurveTilt", ins={"Curve": mc, "Tilt": (mr2, "Result")})

    t1 = xform(ng, sct, rotation=(0, 0, -0.7854))
    t2 = xform(ng, t1, translation=(0, 0, -0.5), rotation=(math.pi / 2, 0, 0))

    cxyz_s = cxyz(ng, x=(gi, "Width"), y=1.0, z=(gi, "Height"))
    t3 = xform(ng, t2, scale=cxyz_s)

    scr = N(ng, "GeometryNodeSetCurveRadius", ins={"Curve": t3, "Radius": 1.0})
    fc = N(ng, "GeometryNodeFilletCurve",
           ins={"Curve": scr, "Count": 8,
                "Radius": (gi, "Fillet Radius"), "Limit Radius": True})
    set_fillet_mode(fc, "POLY")

    ngp = grp(ng, "n_gon_profile", ins={
        "Profile N-gon": (gi, "Profile N-gon"),
        "Profile Width": (gi, "Profile Width"),
        "Profile Aspect Ratio": (gi, "Profile Aspect Ratio"),
        "Profile Fillet Ratio": (gi, "Profile Fillet Ratio"),
    })
    c2m = N(ng, "GeometryNodeCurveToMesh",
            ins={"Curve": fc, "Profile Curve": ngp, "Fill Caps": True})
    t4 = xform(ng, c2m, rotation=(0, 0, math.pi / 2))
    sss = N(ng, "GeometryNodeSetShadeSmooth",
            ins={"Geometry": t4, "Shade Smooth": False})
    L(ng, sss.outputs[0], go.inputs["Geometry"])
    return ng

def build_strecher():
    ng = NG("strecher",
        ins=[("N-gon", "I", 32), ("Profile Width", "F", 0.2)],
        outs=[("Geometry", "G")])
    gi, go = IO(ng)

    cl = N(ng, "GeometryNodeCurvePrimitiveLine",
           ins={"Start": (1.0, 0.0, 1.0), "End": (1.0, 0.0, -1.0)})
    ngc = grp(ng, "n_gon_cylinder", ins={
        "Radius Curve": cl,
        "Height": 1.0,
        "N-gon": (gi, "N-gon"),
        "Profile Width": (gi, "Profile Width"),
        "Aspect Ratio": 1.0,
        "Resolution": 64,
    })
    L(ng, ngc.outputs["Mesh"], go.inputs["Geometry"])
    return ng

# -- Assembly (with SetMaterial nodes) -----------------------------------------

def build_assembly_nodegroup(params):
    leg_style = params["Leg Style"]
    ctrl_pts = params["Leg Curve Control Points"]

    build_n_gon_profile()
    build_n_gon_cylinder()
    build_create_anchors()
    build_create_legs_and_strechers()
    build_generate_table_top()
    build_merge_curve()

    if leg_style == "straight":
        leg_ng = build_generate_leg_straight(ctrl_pts)
        strecher_ng = build_strecher()
    elif leg_style == "single_stand":
        leg_ng = build_generate_single_stand(ctrl_pts)
        strecher_ng = None
    elif leg_style == "square":
        leg_ng = build_generate_leg_square()
        strecher_ng = None
    else:
        raise NotImplementedError(f"Unknown leg style: {leg_style}")

    ng = NG("assemble_table", ins=[("Geometry", "G")], outs=[("Geometry", "G")])
    gi, go = IO(ng)

    gtt = grp(ng, "generate_table_top", ins={
        "Thickness": params["Top Thickness"],
        "N-gon": params["Top Profile N-gon"],
        "Profile Width": params["Top Profile Width"],
        "Aspect Ratio": params["Top Profile Aspect Ratio"],
        "Fillet Ratio": params["Top Profile Fillet Ratio"],
        "Fillet Radius Vertical": params["Top Vertical Fillet Ratio"],
    })
    tf_top = N(ng, _XFORM,
               ins={"Geometry": (gtt, "Geometry"), "Translation": (0, 0, params["Top Height"])})

    # === SetMaterial for table top ===
    set_mat_top = N(ng, "GeometryNodeSetMaterial",
                    ins={"Geometry": tf_top})
    set_mat_top.inputs["Material"].default_value = MAT_TOP

    anch = grp(ng, "create_anchors", ins={
        "Profile N-gon": params["Leg Number"],
        "Profile Width": params["Leg Placement Top Relative Scale"] * params["Top Profile Width"],
        "Profile Aspect Ratio": params["Top Profile Aspect Ratio"],
    })

    leg = N(ng, _GRP)
    leg.node_tree = leg_ng

    if leg_style == "straight":
        leg.inputs["Leg Height"].default_value = params["Leg Height"]
        leg.inputs["Leg Diameter"].default_value = params["Leg Diameter"]
        leg.inputs["Resolution"].default_value = 32
        leg.inputs["N-gon"].default_value = params["Leg NGon"]
        leg.inputs["Fillet Ratio"].default_value = 0.1

        strecher = N(ng, _GRP)
        strecher.node_tree = strecher_ng
        strecher.inputs["Profile Width"].default_value = params["Leg Diameter"] * 0.5

        las = grp(ng, "create_legs_and_strechers", ins={
            "Anchors": anch,
            "Keep Legs": True,
            "Leg Instance": leg,
            "Table Height": params["Top Height"],
            "Strecher Instance": strecher,
            "Strecher Index Increment": params["Strecher Increament"],
            "Strecher Relative Position": params["Strecher Relative Pos"],
            "Leg Bottom Relative Scale": params["Leg Placement Bottom Relative Scale"],
            "Align Leg X rot": True,
        })

    elif leg_style == "single_stand":
        leg.inputs["Leg Height"].default_value = params["Leg Height"]
        leg.inputs["Leg Diameter"].default_value = params["Leg Diameter"]
        leg.inputs["Resolution"].default_value = 64

        las = grp(ng, "create_legs_and_strechers", ins={
            "Anchors": anch,
            "Keep Legs": True,
            "Leg Instance": leg,
            "Table Height": params["Top Height"],
            "Leg Bottom Relative Scale": params["Leg Placement Bottom Relative Scale"],
            "Align Leg X rot": True,
        })

    elif leg_style == "square":
        leg.inputs["Height"].default_value = params["Leg Height"]
        leg.inputs["Width"].default_value = (
            0.707 * params["Leg Placement Top Relative Scale"]
            * params["Top Profile Width"]
            * params["Top Profile Aspect Ratio"]
        )
        leg.inputs["Has Bottom Connector"].default_value = bool(params["Strecher Increament"] > 0)
        leg.inputs["Profile Width"].default_value = params["Leg Diameter"]

        las = grp(ng, "create_legs_and_strechers", ins={
            "Anchors": anch,
            "Keep Legs": True,
            "Leg Instance": leg,
            "Table Height": params["Top Height"],
            "Leg Bottom Relative Scale": params["Leg Placement Bottom Relative Scale"],
            "Align Leg X rot": True,
        })

    # === SetMaterial for legs ===
    set_mat_leg = N(ng, "GeometryNodeSetMaterial",
                    ins={"Geometry": las})
    set_mat_leg.inputs["Material"].default_value = MAT_LEG

    join = N(ng, "GeometryNodeJoinGeometry")
    L(ng, set_mat_top.outputs[0], join.inputs["Geometry"])
    L(ng, set_mat_leg.outputs[0], join.inputs["Geometry"])
    L(ng, join.outputs[0], go.inputs["Geometry"])
    return ng

# -- Parameters ---------------------------------------------------------------

def sample_parameters():
    dimensions = (np.random.uniform(1, 1.5), np.random.uniform(0.6, 0.9), np.random.uniform(0.4, 0.5))
    x, y, z = dimensions

    leg_style = np.random.choice(["straight", "single_stand", "square"], p=[0.5, 0.1, 0.4])

    if leg_style == "single_stand":
        leg_number = 2
        leg_diameter = np.random.uniform(0.22 * x, 0.28 * x)
        leg_curve_ctrl_pts = [
            (0.0, np.random.uniform(0.1, 0.2)),
            (0.5, np.random.uniform(0.1, 0.2)),
            (0.9, np.random.uniform(0.2, 0.3)),
            (1.0, 1.0),
        ]
        top_scale = np.random.uniform(0.6, 0.7)
        bottom_scale = 1.0
    elif leg_style == "square":
        leg_number = 2
        leg_diameter = np.random.uniform(0.07, 0.10)
        leg_curve_ctrl_pts = None
        top_scale = 0.8
        bottom_scale = 1.0
    elif leg_style == "straight":
        leg_diameter = np.random.uniform(0.05, 0.07)
        leg_number = 4
        leg_curve_ctrl_pts = [
            (0.0, 1.0),
            (0.4, np.random.uniform(0.85, 0.95)),
            (1.0, np.random.uniform(0.4, 0.6)),
        ]
        top_scale = 0.8
        bottom_scale = np.random.uniform(1.0, 1.2)
    else:
        raise NotImplementedError

    top_thickness = np.random.uniform(0.03, 0.06)

    return {
        "Top Profile N-gon": 4,
        "Top Profile Width": 1.414 * x,
        "Top Profile Aspect Ratio": y / x,
        "Top Profile Fillet Ratio": np.random.uniform(0.0, 0.02),
        "Top Thickness": top_thickness,
        "Top Vertical Fillet Ratio": np.random.uniform(0.1, 0.3),
        "Height": z,
        "Top Height": z - top_thickness,
        "Leg Number": leg_number,
        "Leg Style": leg_style,
        "Leg NGon": 4,
        "Leg Placement Top Relative Scale": top_scale,
        "Leg Placement Bottom Relative Scale": bottom_scale,
        "Leg Height": 1.0,
        "Leg Diameter": leg_diameter,
        "Leg Curve Control Points": leg_curve_ctrl_pts,
        "Strecher Relative Pos": np.random.uniform(0.2, 0.6),
        "Strecher Increament": np.random.choice([0, 1]),
    }

def main():
    params = sample_parameters()
    assembly_ng = build_assembly_nodegroup(params)

    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = "CoffeeTableFactory"

    mod = obj.modifiers.new("GeometryNodes", "NODES")
    mod.node_group = assembly_ng

    select_only(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    fallback = next((mat for mat in obj.data.materials if mat is not None), None)
    if fallback is not None:
        for i in range(len(obj.data.materials)):
            if obj.data.materials[i] is None:
                obj.data.materials[i] = fallback

main()

