# [FL_INDEX: keywords="blender_factory, procedural_3d, TableCocktailFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: TableCocktailFactory | Category: factories_tex
# Prompt: A 3D model of a tall cocktail bar table rendered from an elevated three-quarter perspective, featuring a small circular top mounted on a single central pedestal stem that tapers and flares outward into a wide rounded base at the bottom.

import os
import bpy, bmesh, math
import random, colorsys
import numpy as np
from numpy.random import uniform

# ----------------------------------------------------------------------------
# Sources translated faithfully from:

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
    """Set Principled BSDF inputs with Blender-version-tolerant socket names."""

    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Specular": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
        "Sheen Weight": ("Sheen Weight", "Sheen"),
        "Transmission Weight": ("Transmission Weight", "Transmission"),
        "Subsurface Weight": ("Subsurface Weight", "Subsurface"),
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
# Material constructors
# ----------------------------------------------------------------------------

def make_marble(name="Marble") -> bpy.types.Material:
    """Re-impl of materials/ceramic/marble.py:shader_marble."""

    mat = _new_material(name)
    nt = mat.node_tree

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    scale_vec = nt.nodes.new("ShaderNodeVectorMath")
    scale_vec.operation = "SCALE"
    nt.links.new(tex_coord.outputs["Object"], scale_vec.inputs[0])

    vec_rotate = nt.nodes.new("ShaderNodeVectorRotate")
    vec_rotate.rotation_type = "EULER_XYZ"
    nt.links.new(scale_vec.outputs["Vector"], vec_rotate.inputs["Vector"])

    seed_val = nt.nodes.new("ShaderNodeValue")
    seed_val.outputs[0].default_value = 0.0

    scale_val = nt.nodes.new("ShaderNodeValue")
    scale_val.outputs[0].default_value = 3.0

    add_scale = nt.nodes.new("ShaderNodeMath")
    add_scale.inputs[1].default_value = 1.0
    nt.links.new(scale_val.outputs[0], add_scale.inputs[0])

    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise2, "noise_dimensions"):
        try: noise2.noise_dimensions = "4D"
        except TypeError: pass
    noise2.inputs["Scale"].default_value = 4.0  # add output
    if "Detail" in noise2.inputs: noise2.inputs["Detail"].default_value = 15.0
    if "W" in noise2.inputs: nt.links.new(seed_val.outputs[0], noise2.inputs["W"])
    nt.links.new(vec_rotate.outputs["Vector"], noise2.inputs["Vector"])
    nt.links.new(add_scale.outputs[0], noise2.inputs["Scale"])

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[1].default_value = 0.48
    map_range.inputs[2].default_value = 0.60
    nt.links.new(_noise_fac_output(noise2), map_range.inputs[0])

    noise_main = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise_main, "noise_dimensions"):
        try: noise_main.noise_dimensions = "4D"
        except TypeError: pass
    if "Detail" in noise_main.inputs: noise_main.inputs["Detail"].default_value = 15.0
    if "W" in noise_main.inputs: nt.links.new(seed_val.outputs[0], noise_main.inputs["W"])
    nt.links.new(vec_rotate.outputs["Vector"], noise_main.inputs["Vector"])
    nt.links.new(scale_val.outputs[0], noise_main.inputs["Scale"])

    noise3 = nt.nodes.new("ShaderNodeTexNoise")
    noise3.inputs["Scale"].default_value = 8.0
    if "Detail" in noise3.inputs: noise3.inputs["Detail"].default_value = 15.0
    nt.links.new(_noise_fac_output(noise_main), noise3.inputs["Vector"])

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(voronoi, "voronoi_dimensions"):
        try: voronoi.voronoi_dimensions = "4D"
        except TypeError: voronoi.voronoi_dimensions = "3D"
    if hasattr(voronoi, "feature"):
        try: voronoi.feature = "DISTANCE_TO_EDGE"
        except TypeError: pass
    voronoi.inputs["Scale"].default_value = 3.0
    if "W" in voronoi.inputs: voronoi.inputs["W"].default_value = 1.64
    nt.links.new(_noise_fac_output(noise3), voronoi.inputs["Vector"])

    dist_out = voronoi.outputs.get("Distance") or voronoi.outputs[0]
    cr1 = nt.nodes.new("ShaderNodeValToRGB")
    cr1_fac = cr1.inputs.get("Fac") or cr1.inputs[0]
    nt.links.new(dist_out, cr1_fac)
    cr1.color_ramp.elements[0].position = 0.0
    cr1.color_ramp.elements[0].color = (1, 1, 1, 1)
    cr1.color_ramp.elements[1].position = 0.03
    cr1.color_ramp.elements[1].color = (0, 0, 0, 1)

    multiply = nt.nodes.new("ShaderNodeMath")
    multiply.operation = "MULTIPLY"
    nt.links.new(map_range.outputs["Result"], multiply.inputs[0])
    nt.links.new(cr1.outputs["Color"], multiply.inputs[1])

    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise1, "noise_dimensions"):
        try: noise1.noise_dimensions = "4D"
        except TypeError: pass
    noise1.inputs["Scale"].default_value = 8.0
    if "Detail" in noise1.inputs: noise1.inputs["Detail"].default_value = 15.0
    if "W" in noise1.inputs: nt.links.new(seed_val.outputs[0], noise1.inputs["W"])
    nt.links.new(_noise_fac_output(noise_main), noise1.inputs["Vector"])

    mix1 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix1, "data_type"):
        mix1.data_type = "RGBA"
    mix1.inputs[0].default_value = 0.8
    nt.links.new(_noise_fac_output(noise_main), mix1.inputs[6])
    nt.links.new(_noise_fac_output(noise1), mix1.inputs[7])

    cr0 = nt.nodes.new("ShaderNodeValToRGB")
    cr0_fac = cr0.inputs.get("Fac") or cr0.inputs[0]
    nt.links.new(mix1.outputs[2], cr0_fac)
    cr0.color_ramp.elements[0].position = 0.3
    cr0.color_ramp.elements[0].color = (1, 1, 1, 1)
    cr0.color_ramp.elements[1].position = 0.9
    cr0.color_ramp.elements[1].color = (0, 0, 0, 1)

    mix0 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix0, "data_type"):
        mix0.data_type = "RGBA"
    nt.links.new(multiply.outputs[0], mix0.inputs[0])
    nt.links.new(cr0.outputs["Color"], mix0.inputs[6])
    mix0.inputs[7].default_value = (0.0376, 0.0179, 0.0033, 1.0)

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.02
    nt.links.new(multiply.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=0.1, **{"Specular IOR Level": 0.6})
    nt.links.new(mix1.outputs[2], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_tiled_wood(name="TiledWood") -> bpy.types.Material:
    """Re-impl of materials/wood/tiled_wood.py:shader_wood_tiled.

    Uses BrickTexture for tiling and NoiseTexture (replacing MusgraveTexture
    removed in Blender 5.0) for wood grain patterns.
    """
    # Sample parameters as in original
    hscale = float(np.clip(np.random.normal(6, 4), 3, 9))
    vscale = float(np.random.uniform(0.05, 0.2)) * hscale
    tile_seed = float(np.random.uniform(-1000.0, 1000.0))
    # base_color from wood.get_color()
    bark_h, bark_s, bark_v = bark_hsv()
    base_color = hsv2rgba((bark_h + np.random.uniform(-0.0, 0.05),
                           max(0.0, bark_s + np.random.uniform(-0.3, 0.2)),
                           bark_v * _mat_log_uniform(0.2, 20)))
    roughness_lo = float(np.random.uniform(0.3, 0.5))
    roughness_hi = float(np.random.uniform(0.8, 1.0))
    mapping_offset = np.random.uniform(0, 1, 3).tolist()

    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # === Tiling sub-graph (nodegroup_tiling) ===
    div_h = 1.0 / hscale
    div_v = 1.0 / vscale

    mapping_tile = nt.nodes.new("ShaderNodeMapping")
    mapping_tile.inputs["Location"].default_value = mapping_offset
    nt.links.new(tex_coord.outputs["Object"], mapping_tile.inputs["Vector"])

    cxyz_offset = nt.nodes.new("ShaderNodeCombineXYZ")
    cxyz_offset.inputs["Y"].default_value = div_h
    add_vec = nt.nodes.new("ShaderNodeVectorMath")
    nt.links.new(mapping_tile.outputs["Vector"], add_vec.inputs[0])
    nt.links.new(cxyz_offset.outputs[0], add_vec.inputs[1])

    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Mortar Size"].default_value = 0.005
    brick.inputs["Mortar Smooth"].default_value = 1.0
    brick.inputs["Bias"].default_value = -0.5
    brick.inputs["Brick Width"].default_value = div_v
    brick.inputs["Row Height"].default_value = div_h
    brick.inputs["Color2"].default_value = (0, 0, 0, 1)
    if hasattr(brick, "squash_frequency"):
        brick.squash_frequency = 1
    nt.links.new(add_vec.outputs["Vector"], brick.inputs["Vector"])

    # tile_seed: multiply_add(brick_color * 1000 + seed)
    mul_add_seed = nt.nodes.new("ShaderNodeMath")
    mul_add_seed.operation = "MULTIPLY_ADD"
    mul_add_seed.inputs[1].default_value = 1000.0
    mul_add_seed.inputs[2].default_value = tile_seed
    nt.links.new(brick.outputs["Color"], mul_add_seed.inputs[0])

    # === Wood grain (replacing Musgrave with Noise) ===
    mapping_grain = nt.nodes.new("ShaderNodeMapping")
    mapping_grain.inputs["Scale"].default_value = (5.0, 100.0, 100.0)
    nt.links.new(tex_coord.outputs["Object"], mapping_grain.inputs["Vector"])

    # musgrave_texture_2 substitute: noise with 4D seed
    noise_musgrave2 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise_musgrave2, "noise_dimensions"):
        try: noise_musgrave2.noise_dimensions = "4D"
        except TypeError: pass
    noise_musgrave2.inputs["Scale"].default_value = 10.0
    if "Detail" in noise_musgrave2.inputs: noise_musgrave2.inputs["Detail"].default_value = 15.0
    if "W" in noise_musgrave2.inputs:
        nt.links.new(mul_add_seed.outputs[0], noise_musgrave2.inputs["W"])
    nt.links.new(mapping_grain.outputs["Vector"], noise_musgrave2.inputs["Vector"])

    mr2 = nt.nodes.new("ShaderNodeMapRange")
    mr2.inputs[3].default_value = 1.0
    mr2.inputs[4].default_value = -1.0
    nt.links.new(_noise_fac_output(noise_musgrave2), mr2.inputs[0])

    # noise_texture_1
    mapping_mid = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tex_coord.outputs["Object"], mapping_mid.inputs["Vector"])
    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise1, "noise_dimensions"):
        try: noise1.noise_dimensions = "4D"
        except TypeError: pass
    noise1.inputs["Scale"].default_value = 0.5
    if "Detail" in noise1.inputs: noise1.inputs["Detail"].default_value = 1.0
    if "Distortion" in noise1.inputs: noise1.inputs["Distortion"].default_value = 1.1
    if "W" in noise1.inputs:
        nt.links.new(mul_add_seed.outputs[0], noise1.inputs["W"])
    nt.links.new(mapping_mid.outputs["Vector"], noise1.inputs["Vector"])

    # musgrave_texture_1 substitute
    noise_musgrave1 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise_musgrave1, "noise_dimensions"):
        try: noise_musgrave1.noise_dimensions = "4D"
        except TypeError: pass
    if "Detail" in noise_musgrave1.inputs: noise_musgrave1.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise_musgrave1.inputs: noise_musgrave1.inputs["Distortion"].default_value = 0.5
    if "W" in noise_musgrave1.inputs:
        nt.links.new(mul_add_seed.outputs[0], noise_musgrave1.inputs["W"])
    nt.links.new(_noise_fac_output(noise1), noise_musgrave1.inputs["Vector"])

    mr1 = nt.nodes.new("ShaderNodeMapRange")
    mr1.inputs[3].default_value = -1.4
    mr1.inputs[4].default_value = 1.5
    nt.links.new(_noise_fac_output(noise_musgrave1), mr1.inputs[0])

    mr1b = nt.nodes.new("ShaderNodeMapRange")
    mr1b.inputs[3].default_value = 1.0
    mr1b.inputs[4].default_value = 0.5
    nt.links.new(mr1.outputs["Result"], mr1b.inputs[0])

    # noise_texture (ring pattern)
    mapping_ring = nt.nodes.new("ShaderNodeMapping")
    mapping_ring.inputs["Scale"].default_value = (0.15, 1.0, 0.15)
    nt.links.new(tex_coord.outputs["Object"], mapping_ring.inputs["Vector"])

    noise_ring = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise_ring, "noise_dimensions"):
        try: noise_ring.noise_dimensions = "4D"
        except TypeError: pass
    if "Detail" in noise_ring.inputs: noise_ring.inputs["Detail"].default_value = 5.0
    if "Distortion" in noise_ring.inputs: noise_ring.inputs["Distortion"].default_value = 1.0
    if "W" in noise_ring.inputs:
        nt.links.new(mul_add_seed.outputs[0], noise_ring.inputs["W"])
    nt.links.new(mapping_ring.outputs["Vector"], noise_ring.inputs["Vector"])

    # musgrave_texture substitute (final ring)
    noise_musgrave0 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise_musgrave0, "noise_dimensions"):
        try: noise_musgrave0.noise_dimensions = "4D"
        except TypeError: pass
    noise_musgrave0.inputs["Scale"].default_value = 4.0
    if "Detail" in noise_musgrave0.inputs: noise_musgrave0.inputs["Detail"].default_value = 10.0
    if "W" in noise_musgrave0.inputs:
        nt.links.new(mul_add_seed.outputs[0], noise_musgrave0.inputs["W"])
    nt.links.new(_noise_fac_output(noise_ring), noise_musgrave0.inputs["Vector"])

    # mix: ring pattern
    mix_ring = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_ring, "data_type"):
        mix_ring.data_type = "RGBA"
    nt.links.new(_noise_fac_output(noise_ring), mix_ring.inputs[6])
    nt.links.new(_noise_fac_output(noise_musgrave0), mix_ring.inputs[7])

    # mix_1: multiply blend with mr1b
    mix_1 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_1, "data_type"):
        mix_1.data_type = "RGBA"
    if hasattr(mix_1, "blend_type"):
        try: mix_1.blend_type = "MULTIPLY"
        except TypeError: pass
    mix_1.inputs[0].default_value = 0.9
    nt.links.new(mr1b.outputs["Result"], mix_1.inputs[6])
    nt.links.new(mix_ring.outputs[2], mix_1.inputs[7])

    # mix_2: multiply blend with mr2
    mix_2 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_2, "data_type"):
        mix_2.data_type = "RGBA"
    if hasattr(mix_2, "blend_type"):
        try: mix_2.blend_type = "MULTIPLY"
        except TypeError: pass
    mix_2.inputs[0].default_value = 0.95
    nt.links.new(mr2.outputs["Result"], mix_2.inputs[6])
    nt.links.new(mix_1.outputs[2], mix_2.inputs[7])

    # hue_saturation
    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Saturation"].default_value = 0.8
    hsv_node.inputs["Value"].default_value = 0.2
    hsv_node.inputs["Fac"].default_value = 0.0
    hsv_node.inputs["Color"].default_value = base_color

    # mix_3: combine hsv + base_color by mix_2 factor
    mix_3 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_3, "data_type"):
        mix_3.data_type = "RGBA"
    nt.links.new(mix_2.outputs[2], mix_3.inputs[0])
    nt.links.new(hsv_node.outputs["Color"], mix_3.inputs[6])
    mix_3.inputs[7].default_value = base_color

    # mix_4: multiply with tile color
    mix_4 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_4, "data_type"):
        mix_4.data_type = "RGBA"
    if hasattr(mix_4, "blend_type"):
        try: mix_4.blend_type = "MULTIPLY"
        except TypeError: pass
    mix_4.inputs[0].default_value = 1.0
    nt.links.new(mix_3.outputs[2], mix_4.inputs[6])
    nt.links.new(brick.outputs["Color"], mix_4.inputs[7])

    # roughness from float curve
    fc = _build_float_curve(nt, mix_4.outputs[2], [(0, roughness_lo), (1, roughness_hi)])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix_4.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])

    # Displacement: brick displacement + grain * 0.1 -> * 0.01
    mul_grain_disp = nt.nodes.new("ShaderNodeMath")
    mul_grain_disp.operation = "MULTIPLY"
    mul_grain_disp.inputs[1].default_value = 0.1
    nt.links.new(mix_2.outputs[2], mul_grain_disp.inputs[0])
    add_disp = nt.nodes.new("ShaderNodeMath")
    nt.links.new(brick.outputs["Color"], add_disp.inputs[0])
    nt.links.new(mul_grain_disp.outputs[0], add_disp.inputs[1])
    mul_total_disp = nt.nodes.new("ShaderNodeMath")
    mul_total_disp.operation = "MULTIPLY"
    mul_total_disp.inputs[1].default_value = 0.01
    nt.links.new(add_disp.outputs[0], mul_total_disp.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_total_disp.outputs[0], disp.inputs["Height"])

    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_wood(name="Wood", color=None) -> bpy.types.Material:
    """Re-impl of materials/wood/wood.py:shader_wood.

    Original uses MusgraveTexture (removed in Blender 5.0). We substitute
    multi-octave NoiseTexture in stretched mapping to fake the grain look.
    """

    if color is None:
        bark_h, bark_s, bark_v = bark_hsv()
        color = hsv2rgba((bark_h + np.random.uniform(-0.0, 0.05),
                          max(0.0, bark_s + np.random.uniform(-0.3, 0.2)),
                          bark_v * _mat_log_uniform(0.2, 20)))
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (5.0, 100.0, 100.0)
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    grain = nt.nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 10.0
    if "Detail" in grain.inputs: grain.inputs["Detail"].default_value = 15.0
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

    roughness_val = float(np.random.uniform(0.0, 1.0))
    seed_val = float(np.random.uniform(-1000.0, 1000.0))
    if base_color is None:
        base_color = hsv2rgba((np.random.uniform(0, 1),
                               np.random.uniform(0.5, 0.8),
                               _mat_log_uniform(0.01, 0.5)))
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[0].default_value = roughness_val
    mr.inputs[3].default_value = 0.05
    mr.inputs[4].default_value = 0.25

    noise = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise, "noise_dimensions"):
        try: noise.noise_dimensions = "4D"
        except TypeError: pass
    noise.inputs["Scale"].default_value = 2000.0
    if "Detail" in noise.inputs: noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs: noise.inputs["W"].default_value = seed_val
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

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

def make_glass_volume(name="GlassVolume") -> bpy.types.Material:
    """Re-impl of materials/ceramic/glass_volume.py."""

    if np.random.uniform() < 0.3:
        color = (1, 1, 1, 1)
    else:
        color = hsv2rgba((np.random.uniform(0, 1),
                          np.random.uniform(0.5, 0.9),
                          np.random.uniform(0.6, 0.9)))
    density = 100.0
    mat = _new_material(name)
    nt = mat.node_tree

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=0.0, **{"Transmission Weight": 1.0})

    vol = nt.nodes.new("ShaderNodeVolumeAbsorption")
    vol.inputs["Color"].default_value = color
    vol.inputs["Density"].default_value = density

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    nt.links.new(vol.outputs[0], out.inputs["Volume"])
    return mat

def make_ceramic(name="Ceramic") -> bpy.types.Material:
    """Re-impl of materials/ceramic/ceramic.py:shader_ceramic."""

    if np.random.uniform() < 0.8:
        color = hsv2rgba((np.random.uniform(0, 1),
                          np.random.uniform(0.2, 0.4),
                          _mat_log_uniform(0.3, 0.6)))
    else:
        color = hsv2rgba((0, 0, _mat_log_uniform(0.3, 0.6)))

    roughness_min = 0
    roughness_max = 0.8
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # Roughness from noise -> float curve (replaces nw.musgrave)
    noise_r = nt.nodes.new("ShaderNodeTexNoise")
    noise_r.inputs["Scale"].default_value = _mat_log_uniform(20, 40)
    nt.links.new(tex_coord.outputs["Generated"], noise_r.inputs["Vector"])
    fc_r = _build_float_curve(nt, _noise_fac_output(noise_r),
                              [(0, roughness_min), (1, roughness_max)])

    # Coat roughness from noise -> float curve
    noise_c = nt.nodes.new("ShaderNodeTexNoise")
    noise_c.inputs["Scale"].default_value = _mat_log_uniform(20, 40)
    nt.links.new(tex_coord.outputs["Generated"], noise_c.inputs["Vector"])
    fc_c = _build_float_curve(nt, _noise_fac_output(noise_c),
                              [(0, roughness_min), (1, roughness_max)])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf,
                    **{"Base Color": color,
                       "Specular IOR Level": 1.0,
                       "Coat Weight": 1.0,
                       "Subsurface Weight": float(np.random.uniform(0.02, 0.05)),
                       "Subsurface Radius": (0.02, 0.02, 0.02)})
    nt.links.new(fc_r.outputs["Value"], bsdf.inputs["Roughness"])
    if "Coat Roughness" in bsdf.inputs:
        nt.links.new(fc_c.outputs["Value"], bsdf.inputs["Coat Roughness"])
    elif "Clearcoat Roughness" in bsdf.inputs:
        nt.links.new(fc_c.outputs["Value"], bsdf.inputs["Clearcoat Roughness"])

    # Displacement
    noise_d = nt.nodes.new("ShaderNodeTexNoise")
    noise_d.inputs["Scale"].default_value = _mat_log_uniform(20, 40)
    disp_scale = _mat_log_uniform(0.001, 0.005)
    mul_d = nt.nodes.new("ShaderNodeMath")
    mul_d.operation = "MULTIPLY"
    mul_d.inputs[1].default_value = disp_scale
    nt.links.new(_noise_fac_output(noise_d), mul_d.inputs[0])
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_d.outputs[0], disp.inputs["Height"])

    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_glass(name="Glass") -> bpy.types.Material:
    """Re-impl of materials/ceramic/glass.py:shader_glass."""

    if np.random.uniform() < 0.5:
        color = (1, 1, 1, 1)
    else:
        color = hsv2rgba((np.random.uniform(0, 1),
                          np.random.uniform(0.05, 0.25), 1))

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

def make_plastic(name="Plastic") -> bpy.types.Material:
    """Re-impl of materials/plastic/plastic.py:Plastic.

    Dispatches between rough and translucent plastic.
    """

    is_rough = float(np.random.uniform(0, 1))
    is_translucent = float(np.random.uniform(0, 1))
    clear = np.random.uniform() < 0.2
    if is_rough > is_translucent:
        return make_plastic_rough(name=name)
    else:
        return _make_plastic_translucent(name=name, clear=clear)

def _make_plastic_translucent(name="PlasticTranslucent", clear=False) -> bpy.types.Material:
    """Re-impl of materials/plastic/plastic_translucent.py."""

    blend_val = float(random.random() * 0.2 + 0.2)
    if clear:
        base_color = hsv2rgba((0, 0, _mat_log_uniform(0.4, 0.8)))
    else:
        base_color = hsv2rgba((np.random.uniform(0, 1),
                               np.random.uniform(0.5, 0.8),
                               _mat_log_uniform(0.4, 0.8)))
    ior_val = float(random.random() * 0.4 + 1.2)

    mat = _new_material(name)
    nt = mat.node_tree

    layer_weight = nt.nodes.new("ShaderNodeLayerWeight")
    layer_weight.inputs["Blend"].default_value = blend_val

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

def make_metal_basic(name="MetalBasic") -> bpy.types.Material:
    """Re-impl of materials/metal/metal_basic.py:shader_metal."""

    color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(np.random.uniform(10, 25))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    roughness_lo = float(np.random.uniform(0, 0.2))
    roughness_hi = float(np.random.uniform(0.4, 0.7))
    fc = _build_float_curve(nt, _noise_fac_output(noise),
                            [(0, roughness_lo), (1, roughness_hi)])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf,
                    Metallic=1.0,
                    **{"Specular IOR Level": float(np.random.uniform(0.5, 1.0)),
                       "Base Color": hsv2rgba(color_hsv)})
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

# ----------------------------------------------------------------------------
# Registries — mirror material_assignments.py entries used by TableCocktailFactory
# ----------------------------------------------------------------------------
# material_assignments.py:191-197 — table_top
TABLE_TOP = [
    (make_marble,        1.0),
    (make_tiled_wood,    1.0),
    (make_wood,          1.0),
    (make_plastic_rough, 0.5),
    (make_glass_volume,  1.0),
]

# material_assignments.py:199-205 — tableware (used for legs)
TABLEWARE = [
    (make_ceramic,     1.0),
    (make_glass,       1.0),
    (make_plastic,     1.0),
    (make_metal_basic, 1.0),
    (make_wood,        1.0),
]

REGISTRY = {
    "table_top": TABLE_TOP,
    "tableware": TABLEWARE,
}

def get_material(registry_key: str, name: str = None) -> bpy.types.Material:
    ctor = weighted_sample_mat(REGISTRY[registry_key])
    return ctor(name=name or registry_key.title())

# wear_tear post-processing — faithful raw-bpy translation
WEAR_TEAR_PROB = [0.5, 0.5]
SCRATCH_LABEL = "scratch"
EDGE_WEAR_LABEL = "wear_tear"

def _find_node(nt, bl_idname):
    return next((n for n in nt.nodes if n.bl_idname == bl_idname), None)

def _s_math(nt, op, in0=None, in1=None, clamp=False):
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

def _s_vmath(nt, op, in0=None, in1=None, scale=None):
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

def _s_noise_tex(nt, vector_socket, scale, detail=2.0, distortion=0.0, roughness=0.5):
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
    noise1 = _s_noise_tex(nt, map1.outputs["Vector"], n_scale.outputs[0],
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
    noise2 = _s_noise_tex(nt, map2.outputs["Vector"], n_scale.outputs[0],
                          detail=15.0, distortion=22.8, roughness=0.0)

    add = _s_math(nt, "ADD", _noise_fac_output(noise1), _noise_fac_output(noise2))

    map3 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map3, "vector_type"):
        try: map3.vector_type = "TEXTURE"
        except TypeError: pass
    map3.inputs["Rotation"].default_value = (0.1588, -0.5742, 0.1920)
    nt.links.new(tex_coord.outputs["Object"], map3.inputs["Vector"])
    noise3 = _s_noise_tex(nt, map3.outputs["Vector"], n_mask_noise.outputs[0], detail=1.0)
    cr_mask = _color_ramp(nt, _noise_fac_output(noise3),
                          [(0.4109, (0, 0, 0, 1)), (1.0, (1, 1, 1, 1))])
    mul_mask = _s_math(nt, "MULTIPLY", n_mask_ratio.outputs[0], cr_mask.outputs["Color"])
    add_combined = _s_math(nt, "ADD", add.outputs[0], mul_mask.outputs[0], clamp=True)

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
    """Faithful raw-bpy port of wear_tear/scratches.py:Scratches.apply_over."""

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
        except Exception as exc:
            print(f"  [scratches] failed on {mat.name}: {type(exc).__name__}: {exc}")

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

    noise_a = _s_noise_tex(nt, mapping.outputs["Vector"],
                           n_scratch_mask_randomness.outputs[0], detail=1.0)
    cr_a = _color_ramp(nt, _noise_fac_output(noise_a),
                       [(0.4436, (0, 0, 0, 1)), (0.5345, (1, 1, 1, 1))])

    bevel = nt.nodes.new("ShaderNodeBevel")
    bevel.samples = 20
    nt.links.new(n_scratch_radius.outputs[0], bevel.inputs["Radius"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sub = _s_vmath(nt, "SUBTRACT", bevel.outputs[0], geo.outputs["Normal"])
    abs_a = _s_math(nt, "ABSOLUTE", sub.outputs["Vector"])
    cr_b = _color_ramp(nt, abs_a.outputs[0],
                       [(0.0691, (0, 0, 0, 1)), (0.1564, (1, 1, 1, 1))])

    mul_a = _s_math(nt, "MULTIPLY", cr_a.outputs["Color"], cr_b.outputs["Color"], clamp=True)
    mul_a1 = _s_math(nt, "MULTIPLY", n_scratch_opacity.outputs[0], mul_a.outputs[0], clamp=True)

    bevel2 = nt.nodes.new("ShaderNodeBevel")
    bevel2.samples = 20
    nt.links.new(n_worn_radius.outputs[0], bevel2.inputs["Radius"])
    sub2 = _s_vmath(nt, "SUBTRACT", bevel2.outputs[0], geo.outputs["Normal"])
    abs_b = _s_math(nt, "ABSOLUTE", sub2.outputs["Vector"])

    noise_b = _s_noise_tex(nt, mapping.outputs["Vector"],
                           n_worn_mask_randomness.outputs[0], detail=1.0)
    cr_c = _color_ramp(nt, _noise_fac_output(noise_b),
                       [(0.0764, (1, 1, 1, 1)), (0.5709, (0, 0, 0, 1))])
    mul_b = _s_math(nt, "MULTIPLY", abs_b.outputs[0], cr_c.outputs["Color"], clamp=True)
    mul_b1 = _s_math(nt, "MULTIPLY", n_worn_opacity.outputs[0], mul_b.outputs[0], clamp=True)
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
    scale_v = _s_vmath(nt, "SCALE", in0=n_scratch_density.outputs[0], scale=2.0)
    vor_v = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(vor_v, "feature"):
        try: vor_v.feature = "DISTANCE_TO_EDGE"
        except TypeError: pass
    nt.links.new(map_v.outputs["Vector"], vor_v.inputs["Vector"])
    nt.links.new(scale_v.outputs[0], vor_v.inputs["Scale"])

    dist_h = vor_h.outputs.get("Distance") or vor_h.outputs[0]
    dist_v = vor_v.outputs.get("Distance") or vor_v.outputs[0]
    mul_dist = _s_math(nt, "MULTIPLY", dist_h, dist_v, clamp=True)
    cr_e = _color_ramp(nt, mul_dist.outputs[0],
                       [(0.0, (1, 1, 1, 1)), (0.0073, (0, 0, 0, 1))])
    mul_e = _s_math(nt, "MULTIPLY", cr_b.outputs["Color"], cr_e.outputs["Color"], clamp=True)
    mul_f = _s_math(nt, "MULTIPLY", mul_a.outputs[0], mul_e.outputs[0], clamp=True)

    bsdf_worn2 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix.outputs[2], bsdf_worn2.inputs["Base Color"])
    _set_principled(bsdf_worn2, Metallic=0.3855, Roughness=0.0,
                    **{"Specular IOR Level": 0.0})

    mix_shader_2 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mul_a1.outputs[0], mix_shader_2.inputs["Fac"])
    nt.links.new(mix_shader.outputs[0], mix_shader_2.inputs[1])
    nt.links.new(bsdf_worn2.outputs[0], mix_shader_2.inputs[2])

    scale_disp = _s_vmath(nt, "SCALE", in0=mul_f.outputs[0], scale=2.0)
    if original_displacement_node is None:
        total_displacement = scale_disp.outputs[0]
    else:
        add_disp = _s_math(nt, "ADD", original_displacement_node.outputs[0],
                           scale_disp.outputs[0], clamp=True)
        total_displacement = add_disp.outputs[0]

    return mix_shader_2.outputs[0], total_displacement

def apply_edge_wear(obj, **params):
    """Faithful raw-bpy port of wear_tear/edge_wear.py:EdgeWear.apply_over."""

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
        except Exception as exc:
            print(f"  [edge_wear] failed on {mat.name}: {type(exc).__name__}: {exc}")

# ── Phase 1 — Material sampling on raw SEED ──
SEED = int(os.environ.get('SEED', 0))
seed_all(SEED)

# Mirror cocktail_table.py:get_material_params() call order:
#   1. TopMaterial = weighted_sample(table_top)()
#   2. LegMaterial = weighted_sample(tableware)()
#   3. scratch gate
#   4. edge_wear gate
MAT_TOP = get_material("table_top", "TopMaterial")
MAT_LEG = get_material("tableware", "LegMaterial")

_scratch_p, _edge_wear_p = WEAR_TEAR_PROB
WEAR_DO_SCRATCH  = (np.random.uniform() <= _scratch_p)
WEAR_DO_EDGEWEAR = (np.random.uniform() <= _edge_wear_p)

# --- Original geometry code (from objects_blender/tables/TableCocktailFactory.py)
#     with SetMaterial nodes added in build_assembly_nodegroup for per-part
#     material assignment. =====================================================

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    bpy.context.scene.cursor.location = (0, 0, 0)

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

# ── GeoNodes builders ──────────────────────────────────────────────────────────

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

# ── Assembly (with SetMaterial nodes for per-part texturing) ──────────────────

def build_assembly_nodegroup(params, mat_top, mat_leg):
    """Build the full table assembly with per-part material assignment.

    Mirrors geometry_assemble_table + geometry_create_legs which
    use SetMaterial nodes for the tabletop and legs respectively.
    """

    leg_style = params["Leg Style"]
    ctrl_pts = params["Leg Curve Control Points"]

    build_n_gon_profile()
    build_n_gon_cylinder()
    build_create_anchors()
    build_create_legs_and_strechers()
    build_generate_table_top()

    if leg_style == "straight":
        leg_ng = build_generate_leg_straight(ctrl_pts)
        strecher_ng = build_strecher()
    elif leg_style == "single_stand":
        leg_ng = build_generate_single_stand(ctrl_pts)
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
               ins={"Geometry": (gtt, "Geometry"),
                    "Translation": (0, 0, params["Top Height"])})

    # --- SetMaterial for tabletop ---
    set_mat_top = N(ng, "GeometryNodeSetMaterial",
                    ins={"Geometry": tf_top})
    set_mat_top.inputs["Material"].default_value = mat_top

    anch = grp(ng, "create_anchors", ins={
        "Profile N-gon": params["Leg Number"],
        "Profile Width": params["Leg Placement Top Relative Scale"] * params["Top Profile Width"],
        "Profile Aspect Ratio": 1.0,
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

    # --- SetMaterial for legs ---
    set_mat_leg = N(ng, "GeometryNodeSetMaterial",
                    ins={"Geometry": las})
    set_mat_leg.inputs["Material"].default_value = mat_leg

    join = N(ng, "GeometryNodeJoinGeometry")
    L(ng, set_mat_top.outputs[0], join.inputs["Geometry"])
    L(ng, set_mat_leg.outputs[0], join.inputs["Geometry"])
    L(ng, join.outputs[0], go.inputs["Geometry"])
    return ng

# ── Parameters ─────────────────────────────────────────────────────────────────

def sample_parameters():
    x = np.random.uniform(0.5, 0.8)
    z = np.random.uniform(1.0, 1.5)
    dimensions = (x, x, z)
    x, y, z = dimensions

    NGon = np.random.choice([4, 32])
    round_table = (NGon >= 32)

    leg_style = np.random.choice(["straight", "single_stand"])

    if leg_style == "single_stand":
        leg_number = 1
        leg_diameter = np.random.uniform(0.7 * x, 0.9 * x)
        leg_curve_ctrl_pts = [
            (0.0, np.random.uniform(0.1, 0.2)),
            (0.5, np.random.uniform(0.1, 0.2)),
            (0.9, np.random.uniform(0.2, 0.3)),
            (1.0, 1.0),
        ]

    elif leg_style == "straight":
        leg_diameter = np.random.uniform(0.05, 0.07)
        if round_table:
            leg_number = int(np.random.choice([3, 4]))
        else:
            leg_number = int(NGon)
        leg_curve_ctrl_pts = [
            (0.0, 1.0),
            (0.4, np.random.uniform(0.85, 0.95)),
            (1.0, np.random.uniform(0.4, 0.6)),
        ]

    else:
        raise NotImplementedError

    top_thickness = np.random.uniform(0.02, 0.05)

    return {
        "Top Profile N-gon": 32 if round_table else 4,
        "Top Profile Width": x if round_table else 1.414 * x,
        "Top Profile Aspect Ratio": 1.0,
        "Top Profile Fillet Ratio": 0.499 if round_table else np.random.uniform(0.0, 0.05),
        "Top Thickness": top_thickness,
        "Top Vertical Fillet Ratio": np.random.uniform(0.1, 0.3),
        "Height": z,
        "Top Height": z - top_thickness,
        "Leg Number": leg_number,
        "Leg Style": leg_style,
        "Leg NGon": int(np.random.choice([4, 32])),
        "Leg Placement Top Relative Scale": 0.7,
        "Leg Placement Bottom Relative Scale": np.random.uniform(1.1, 1.3),
        "Leg Height": 1.0,
        "Leg Diameter": leg_diameter,
        "Leg Curve Control Points": leg_curve_ctrl_pts,
        "Strecher Relative Pos": np.random.uniform(0.2, 0.6),
        "Strecher Increament": int(np.random.choice([0, 1])),
    }

def build(seed=SEED):
    clear_scene()
    np.random.seed(seed)
    random.seed(seed)

    params = sample_parameters()
    assembly_ng = build_assembly_nodegroup(params, MAT_TOP, MAT_LEG)

    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = "TableCocktailFactory"

    mod = obj.modifiers.new("GeometryNodes", "NODES")
    mod.node_group = assembly_ng

    select_only(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # Shade smooth
    select_only(obj)
    bpy.ops.object.shade_smooth()
    obj.data.update()

    # wear_tear post-processing
    if WEAR_DO_SCRATCH:
        apply_scratches(obj)
    if WEAR_DO_EDGEWEAR:
        apply_edge_wear(obj)
    for i in range(len(obj.data.materials)):
        if obj.data.materials[i] is None:
            obj.data.materials[i] = MAT_TOP

    return obj

build(SEED)

