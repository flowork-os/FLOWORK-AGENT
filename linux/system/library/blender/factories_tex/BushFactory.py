# [FL_INDEX: keywords="blender_factory, procedural_3d, BushFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BushFactory | Category: factories_tex
# Prompt: A 3D model of a bare deciduous bush rendered from a slightly elevated perspective. The bush features a dense, rounded mass of thin woody branches that repeatedly bifurcate into fine twigs, forming an intricate, leafless branching structure.

import colorsys
import math
import os
import random
import sys

import bpy
import bmesh
import numpy as np

SEED = int(os.environ.get("SEED", "0"))

# ═══════════════════════════════════════════════════════════════
# Baked material parameters for seeds 0-59
# ═══════════════════════════════════════════════════════════════
_BAKED_CREATE_LEAF_MATERIAL = {
    0: {'base_h': 0.99165049, 'base_s': 0.68344792, 'base_v': 0.23119902, 't': 0.92839893, 'vein_mix': 0.21135566},
    1: {'t': 0.18140474, 'vein_mix': 0.41562615},
    2: {'t': 0.12552916, 'vein_mix': 0.24649227},
    3: {'t': 0.19470802, 'vein_mix': 0.23405506},
    4: {'base_h': 0.99269266, 'base_s': 0.77993845, 'base_v': 0.3517225, 't': 0.97218809, 'vein_mix': 0.40051507},
    5: {'t': 0.25209737, 'vein_mix': 0.33431168},
    6: {'t': 0.10486134, 'vein_mix': 0.58339783},
    7: {'t': 0.4466054, 'vein_mix': 0.32329417},
    8: {'t': 0.33833733, 'vein_mix': 0.28758139},
    9: {'t': 0.57612558, 'vein_mix': 0.43817577},
    10: {'t': 0.49022899, 'vein_mix': 0.56648423},
    11: {'t': 0.011498175, 'vein_mix': 0.46585534},
    12: {'t': 0.69641012, 'vein_mix': 0.27671236},
    13: {'base_h': 0.97991535, 'base_s': 0.70776347, 'base_v': 0.49020448, 't': 0.99604567, 'vein_mix': 0.34648198},
    14: {'t': 0.61554011, 'vein_mix': 0.24275186},
    15: {'t': 0.42486666, 'vein_mix': 0.25157752},
    16: {'t': 0.0019334626, 'vein_mix': 0.31562118},
    17: {'t': 0.72518715, 'vein_mix': 0.43315307},
    18: {'t': 0.59952319, 'vein_mix': 0.24478097},
    19: {'base_h': 0.18195614, 'base_s': 0.68327346, 'base_v': 0.54983598, 't': 0.84795265, 'vein_mix': 0.43006062},
    20: {'t': 0.12536681, 'vein_mix': 0.20138907},
    21: {'t': 0.17843051, 'vein_mix': 0.49755411},
    22: {'t': 0.67334273, 'vein_mix': 0.49386465},
    23: {'t': 0.28650969, 'vein_mix': 0.26872708},
    24: {'t': 0.56929637, 'vein_mix': 0.36204225},
    25: {'base_h': 0.11150172, 'base_s': 0.62772804, 'base_v': 0.64208449, 't': 0.85836209, 'vein_mix': 0.53825336},
    26: {'t': 0.51154293, 'vein_mix': 0.50570942},
    27: {'t': 0.45639357, 'vein_mix': 0.4344726},
    28: {'t': 0.33524203, 'vein_mix': 0.39582676},
    29: {'base_h': 0.131089, 'base_s': 0.6588897, 'base_v': 0.61185398, 't': 0.81430066, 'vein_mix': 0.41425576},
    30: {'t': 0.63955719, 'vein_mix': 0.44142245},
    31: {'t': 0.6075638, 'vein_mix': 0.29317277},
    32: {'t': 0.20668, 'vein_mix': 0.45528316},
    33: {'t': 0.020861319, 'vein_mix': 0.41281185},
    34: {'t': 0.55768304, 'vein_mix': 0.25479897},
    35: {'t': 0.15906159, 'vein_mix': 0.48730241},
    36: {'t': 0.49374878, 'vein_mix': 0.59185668},
    37: {'t': 0.70921494, 'vein_mix': 0.57783529},
    38: {'t': 0.73163734, 'vein_mix': 0.23410037},
    39: {'t': 0.77087704, 'vein_mix': 0.5260366},
    40: {'base_h': 0.033307367, 'base_s': 0.78669701, 'base_v': 0.44198019, 't': 0.90252886, 'vein_mix': 0.28074154},
    41: {'base_h': 0.16787134, 'base_s': 0.63603795, 'base_v': 0.49095095, 't': 0.81189935, 'vein_mix': 0.51234295},
    42: {'t': 0.73009837, 'vein_mix': 0.52906581},
    43: {'t': 0.6764099, 'vein_mix': 0.47185555},
    44: {'t': 0.59603576, 'vein_mix': 0.59203657},
    45: {'base_h': 0.042815628, 'base_s': 0.65165396, 'base_v': 0.59813216, 't': 0.98476033, 'vein_mix': 0.49792523},
    46: {'t': 0.057623226, 'vein_mix': 0.39795341},
    47: {'t': 0.71516857, 'vein_mix': 0.40408396},
    48: {'t': 0.20592233, 'vein_mix': 0.38617005},
    49: {'t': 0.74524253, 'vein_mix': 0.46194982},
    50: {'t': 0.76703634, 'vein_mix': 0.59215115},
    51: {'t': 0.74449369, 'vein_mix': 0.4376842},
    52: {'t': 0.43639323, 'vein_mix': 0.48392551},
    53: {'base_h': 0.99237358, 'base_s': 0.67452951, 'base_v': 0.43390639, 't': 0.98471744, 'vein_mix': 0.5527858},
    54: {'base_h': 0.10705493, 'base_s': 0.69365676, 'base_v': 0.63787392, 't': 0.83998637, 'vein_mix': 0.26011496},
    55: {'t': 0.74621305, 'vein_mix': 0.49948794},
    56: {'t': 0.32110572, 'vein_mix': 0.43719553},
    57: {'t': 0.70170994, 'vein_mix': 0.44446746},
    58: {'t': 0.19125467, 'vein_mix': 0.469477},
    59: {'t': 0.057861536, 'vein_mix': 0.5134717},
}
_BAKED_CREATE_PETAL_MATERIAL = {
    0: {'h': 0.14165049, 'r': 0.92839893, 's': 0.63344792, 'v': 0.43119902},
    1: {'h': 0.77063153, 'r': 0.18140474, 's': 0.61712164, 'v': 0.78607025},
    2: {'h': 0.85505614, 'r': 0.12552916, 's': 0.59195656, 'v': 0.82515153},
    3: {'h': 0.88715102, 'r': 0.19470802, 's': 0.63719876, 'v': 0.85947242},
    4: {'h': 0.14269266, 'r': 0.97218809, 's': 0.72993845, 'v': 0.5517225},
    5: {'h': 0.80838594, 'r': 0.25209737, 's': 0.56118786, 'v': 0.7091435},
    6: {'h': 0.98924427, 'r': 0.10486134, 's': 0.55870008, 'v': 0.76328442},
    7: {'h': 0.30823544, 'r': 0.4466054, 's': 0.066954092, 'v': 0.91919868},
    8: {'h': 0.91031894, 'r': 0.33833733, 's': 0.53327195, 'v': 0.67557891},
    9: {'h': 0.59543941, 'r': 0.57612558, 's': 0.063518905, 'v': 0.98623361},
    10: {'h': 0.91621058, 'r': 0.49022899, 's': 0.080618566, 'v': 0.87593489},
    11: {'h': 0.80649275, 'r': 0.011498175, 's': 0.64350919, 'v': 0.81047426},
    12: {'h': 0.96917809, 'r': 0.69641012, 's': 0.67101456, 'v': 0.37975772},
    13: {'h': 0.12991535, 'r': 0.99604567, 's': 0.65776347, 'v': 0.69020448},
    14: {'h': 0.96068796, 'r': 0.61554011, 's': 0.68625405, 'v': 0.30974078},
    15: {'h': 0.1289438, 'r': 0.42486666, 's': 0.0091938164, 'v': 0.86020256},
    16: {'h': 0.85102832, 'r': 0.0019334626, 's': 0.51235633, 'v': 0.73278594},
    17: {'h': 0.0082882666, 'r': 0.72518715, 's': 0.68686873, 'v': 0.34645247},
    18: {'h': 0.11195244, 'r': 0.59952319, 's': 0.063951622, 'v': 0.83926916},
    19: {'h': 0.18195614, 'r': 0.84795265, 's': 0.68327346, 'v': 0.54983598},
    20: {'h': 0.83686032, 'r': 0.12536681, 's': 0.62107195, 'v': 0.80002936},
    21: {'h': 0.91195763, 'r': 0.17843051, 's': 0.60124154, 'v': 0.8123118},
    22: {'h': 0.023466163, 'r': 0.67334273, 's': 0.72674793, 'v': 0.50919191},
    23: {'h': 0.89823343, 'r': 0.28650969, 's': 0.63205307, 'v': 0.79190595},
    24: {'h': 0.40510562, 'r': 0.56929637, 's': 0.095804549, 'v': 0.93456715},
    25: {'h': 0.11150172, 'r': 0.85836209, 's': 0.62772804, 'v': 0.64208449},
    26: {'h': 0.76427354, 'r': 0.51154293, 's': 0.090142578, 'v': 0.88682059},
    27: {'h': 0.58618149, 'r': 0.45639357, 's': 0.042183822, 'v': 0.92045829},
    28: {'h': 0.81880266, 'r': 0.33524203, 's': 0.59861902, 'v': 0.77376},
    29: {'h': 0.131089, 'r': 0.81430066, 's': 0.6588897, 'v': 0.61185398},
    30: {'h': 0.010355613, 'r': 0.63955719, 's': 0.72160014, 'v': 0.33975756},
    31: {'h': 0.97329319, 'r': 0.6075638, 's': 0.64812924, 'v': 0.38671862},
    32: {'h': 0.81689324, 'r': 0.20668, 's': 0.62174602, 'v': 0.75058932},
    33: {'h': 0.8051014, 'r': 0.020861319, 's': 0.60595066, 'v': 0.88252344},
    34: {'h': 0.13699743, 'r': 0.55768304, 's': 0.095180628, 'v': 0.925339},
    35: {'h': 0.92813354, 'r': 0.15906159, 's': 0.6263949, 'v': 0.75679498},
    36: {'h': 0.97964171, 'r': 0.49374878, 's': 0.13734902, 'v': 0.95644741},
    37: {'h': 0.044458822, 'r': 0.70921494, 's': 0.72477205, 'v': 0.2076269},
    38: {'h': 0.95852509, 'r': 0.73163734, 's': 0.69407752, 'v': 0.22861293},
    39: {'h': 0.03150915, 'r': 0.77087704, 's': 0.74650685, 'v': 0.29529228},
    40: {'h': 0.18330737, 'r': 0.90252886, 's': 0.73669701, 'v': 0.64198019},
    41: {'h': 0.16787134, 'r': 0.81189935, 's': 0.63603795, 'v': 0.49095095},
    42: {'h': 0.032266453, 'r': 0.73009837, 's': 0.69481919, 'v': 0.5704505},
    43: {'h': 0.017963886, 'r': 0.6764099, 's': 0.66601318, 'v': 0.54822547},
    44: {'h': 0.98009143, 'r': 0.59603576, 's': 0.11789223, 'v': 0.84872894},
    45: {'h': 0.19281563, 'r': 0.98476033, 's': 0.60165396, 'v': 0.79813216},
    46: {'h': 0.049911322, 'r': 0.057623226, 's': 0.58908045, 'v': 0.78786711},
    47: {'h': 0.0010209909, 'r': 0.71516857, 's': 0.67769927, 'v': 0.20956892},
    48: {'h': 0.97367591, 'r': 0.20592233, 's': 0.58988539, 'v': 0.87184304},
    49: {'h': 0.015487455, 'r': 0.74524253, 's': 0.75244274, 'v': 0.3500377},
    50: {'h': 0.048037787, 'r': 0.76703634, 's': 0.70595625, 'v': 0.576172},
    51: {'h': 0.0094210498, 'r': 0.74449369, 's': 0.79610419, 'v': 0.25102856},
    52: {'h': 0.70981378, 'r': 0.43639323, 's': 0.007380894, 'v': 0.90099194},
    53: {'h': 0.14237358, 'r': 0.98471744, 's': 0.62452951, 'v': 0.63390639},
    54: {'h': 0.10705493, 'r': 0.83998637, 's': 0.69365676, 'v': 0.63787392},
    55: {'h': 0.024871985, 'r': 0.74621305, 's': 0.80452268, 'v': 0.5762461},
    56: {'h': 0.9050579, 'r': 0.32110572, 's': 0.60414276, 'v': 0.78155601},
    57: {'h': 0.011116865, 'r': 0.70170994, 's': 0.63394211, 'v': 0.44338352},
    58: {'h': 0.94760586, 'r': 0.19125467, 's': 0.67002569, 'v': 0.80047727},
    59: {'h': 0.83932731, 'r': 0.057861536, 's': 0.65291275, 'v': 0.88427104},
}

# SEED-deterministic: material functions call _seed_mat(seed); geometry uses np.random.seed(SEED_VAL)
def _compute_bush_params(seed):
    import numpy as np
    np.random.seed(seed); shrub_shape = int(np.random.randint(2))
    np.random.seed(seed); leaf_type = 1 if np.random.choice(["leaf_v2","flower","berry"], p=[0.5,0.5,0])=="leaf_v2" else 0
    return shrub_shape, leaf_type
SHRUB_SHAPE, LEAF_TYPE = _compute_bush_params(SEED)
SEED_VAL = SEED


# ═══════════════════════════════════════════════════════════════════════════════
# Material helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _hsv2rgba(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(float(h) % 1, max(0, min(1, float(s))),
                                    max(0, min(1, float(v))))
    return (r, g, b, 1.0)

def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _fac(node):
    """Return the 'Fac' / 'Factor' output (Blender 5.0 renamed it)."""

    return node.outputs.get("Fac") or node.outputs.get("Factor") or node.outputs[0]


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

def _hex2rgb(h):
    return ((h >> 16) & 0xFF) / 255.0, ((h >> 8) & 0xFF) / 255.0, (h & 0xFF) / 255.0

def _bark_base_hsv():
    hexval = WOOD_COLORS[np.random.randint(len(WOOD_COLORS))]
    r, g, b = _hex2rgb(hexval)
    return colorsys.rgb_to_hsv(r, g, b)

def _plant_green():
    return (np.random.uniform(0.25, 0.33),
            np.clip(np.random.normal(0.65, 0.03), 0, 1),
            np.random.uniform(0.1, 0.45))


def create_bark_material(seed):
    base_h, base_s, base_v = _bark_base_hsv()

    mat = _new_mat("BarkMaterial")
    nt = mat.node_tree
    N = nt.nodes
    L = nt.links

    out = N.new('ShaderNodeOutputMaterial')
    bsdf = N.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = 0.85
    L.new(bsdf.outputs[0], out.inputs[0])

    tex_coord = N.new('ShaderNodeTexCoord')

    # ── Color: Voronoi + Noise color variation (matching shader_random_bark_mat) ──
    # Dark bark color  (V shifted down)
    dark_r, dark_g, dark_b = colorsys.hsv_to_rgb(
        base_h, min(1, base_s * 1.1), max(0, base_v * 0.4))
    # Bright bark color (V shifted up)
    bright_r, bright_g, bright_b = colorsys.hsv_to_rgb(
        base_h, max(0, base_s * 0.8), min(1, base_v * 1.5 + 0.1))

    # Voronoi texture for bark crack pattern
    voronoi = N.new('ShaderNodeTexVoronoi')
    voronoi.feature = 'DISTANCE_TO_EDGE'
    voronoi.inputs['Scale'].default_value = float(np.random.uniform(20, 40))
    L.new(tex_coord.outputs['Object'], voronoi.inputs['Vector'])

    map_range = N.new('ShaderNodeMapRange')
    map_range.inputs['From Min'].default_value = 0.0
    map_range.inputs['From Max'].default_value = 0.5
    L.new(voronoi.outputs['Distance'], map_range.inputs['Value'])

    # Noise for additional color variation
    noise_col = N.new('ShaderNodeTexNoise')
    noise_col.inputs['Scale'].default_value = float(np.random.uniform(8, 15))
    noise_col.inputs['Detail'].default_value = 6.0
    L.new(tex_coord.outputs['Object'], noise_col.inputs['Vector'])

    # Mix: dark <-> bright via voronoi
    mix1 = N.new('ShaderNodeMix')
    mix1.data_type = 'RGBA'
    mix1.inputs[6].default_value = (dark_r, dark_g, dark_b, 1)
    mix1.inputs[7].default_value = (bright_r, bright_g, bright_b, 1)
    L.new(map_range.outputs['Result'], mix1.inputs[0])

    # Additional noise-based variation overlay
    mix2 = N.new('ShaderNodeMix')
    mix2.data_type = 'RGBA'
    mix2.inputs[0].default_value = 0.15  # subtle blend
    L.new(mix1.outputs[2], mix2.inputs[6])
    # Slightly shifted bright color for noise
    shifted_r, shifted_g, shifted_b = colorsys.hsv_to_rgb(
        base_h, max(0, base_s * 0.6), min(1, base_v * 1.3))
    mix2.inputs[7].default_value = (shifted_r, shifted_g, shifted_b, 1)
    L.new(_fac(noise_col), mix2.inputs[0])

    L.new(mix2.outputs[2], bsdf.inputs['Base Color'])

    # ── Bump: multi-scale noise (matching geo_bark_random displacement) ──
    # Large-scale bark ridges
    noise_b1 = N.new('ShaderNodeTexNoise')
    noise_b1.inputs['Scale'].default_value = float(np.random.uniform(15, 25))
    noise_b1.inputs['Detail'].default_value = 8.0
    noise_b1.inputs['Roughness'].default_value = 0.7
    L.new(tex_coord.outputs['Object'], noise_b1.inputs['Vector'])

    bump1 = N.new('ShaderNodeBump')
    bump1.inputs['Strength'].default_value = 0.4
    bump1.inputs['Distance'].default_value = 0.02
    L.new(_fac(noise_b1), bump1.inputs['Height'])

    # Fine-scale bark detail
    noise_b2 = N.new('ShaderNodeTexNoise')
    noise_b2.inputs['Scale'].default_value = float(np.random.uniform(40, 80))
    noise_b2.inputs['Detail'].default_value = 4.0
    L.new(tex_coord.outputs['Object'], noise_b2.inputs['Vector'])

    bump2 = N.new('ShaderNodeBump')
    bump2.inputs['Strength'].default_value = 0.15
    bump2.inputs['Distance'].default_value = 0.005
    L.new(_fac(noise_b2), bump2.inputs['Height'])
    L.new(bump1.outputs[0], bump2.inputs['Normal'])

    L.new(bump2.outputs[0], bsdf.inputs['Normal'])

    return mat


def create_leaf_material(seed):

    # 80% green, 10% yellow, 10% red (matching LeafFactoryV2.__init__)
    t = _BAKED_CREATE_LEAF_MATERIAL.get(seed % 60, _BAKED_CREATE_LEAF_MATERIAL[0])['t']
    if t < 0.8:
        base_h, base_s, base_v = _plant_green()
    elif t < 0.9:
        # plant_yellow
        base_h = _BAKED_CREATE_LEAF_MATERIAL.get(seed % 60, _BAKED_CREATE_LEAF_MATERIAL[0])['base_h']
        base_s = _BAKED_CREATE_LEAF_MATERIAL.get(seed % 60, _BAKED_CREATE_LEAF_MATERIAL[0])['base_s']
        base_v = _BAKED_CREATE_LEAF_MATERIAL.get(seed % 60, _BAKED_CREATE_LEAF_MATERIAL[0])['base_v']
    else:
        # plant_red
        base_h = _BAKED_CREATE_LEAF_MATERIAL.get(seed % 60, _BAKED_CREATE_LEAF_MATERIAL[0])['base_h']
        base_s = _BAKED_CREATE_LEAF_MATERIAL.get(seed % 60, _BAKED_CREATE_LEAF_MATERIAL[0])['base_s']
        base_v = _BAKED_CREATE_LEAF_MATERIAL.get(seed % 60, _BAKED_CREATE_LEAF_MATERIAL[0])['base_v']

    base_rgba = _hsv2rgba(base_h, base_s, base_v)
    # Vein color: slightly mixed toward gray (matching shader_leaf_new)
    vein_mix = _BAKED_CREATE_LEAF_MATERIAL.get(seed % 60, _BAKED_CREATE_LEAF_MATERIAL[0])['vein_mix']
    vein_rgba = tuple(base_rgba[i] * (1 - vein_mix) + 0.35 * vein_mix
                      for i in range(3)) + (1.0,)

    mat = _new_mat("LeafMaterial")
    nt = mat.node_tree
    N = nt.nodes
    L = nt.links

    out = N.new('ShaderNodeOutputMaterial')
    tex_coord = N.new('ShaderNodeTexCoord')

    # Noise for vein-like color variation
    noise = N.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = float(np.random.uniform(8, 20))
    noise.inputs['Detail'].default_value = 6.0
    L.new(tex_coord.outputs['Object'], noise.inputs['Vector'])

    # Color ramp: vein color <-> base color
    cr = N.new('ShaderNodeValToRGB')
    cr.color_ramp.color_mode = 'HSV'
    cr.color_ramp.hue_interpolation = 'NEAR'
    L.new(_fac(noise), cr.inputs['Fac'])
    cr.color_ramp.elements[0].position = 0.3
    cr.color_ramp.elements[0].color = vein_rgba
    cr.color_ramp.elements[1].position = 0.7
    cr.color_ramp.elements[1].color = base_rgba

    # Translucent + Principled mix (matching leaf_v2: 0.7 translucent fac)
    trans = N.new('ShaderNodeBsdfTranslucent')
    L.new(cr.outputs['Color'], trans.inputs['Color'])

    bsdf = N.new('ShaderNodeBsdfPrincipled')
    L.new(cr.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.5

    mix_sh = N.new('ShaderNodeMixShader')
    mix_sh.inputs['Fac'].default_value = 0.7
    L.new(trans.outputs[0], mix_sh.inputs[1])
    L.new(bsdf.outputs[0], mix_sh.inputs[2])

    L.new(mix_sh.outputs[0], out.inputs['Surface'])

    return mat


def create_petal_material(seed):

    # tree_petal_hsv: 40% pink, 20% white, 20% red, 20% yellow
    r = _BAKED_CREATE_PETAL_MATERIAL.get(seed % 60, _BAKED_CREATE_PETAL_MATERIAL[0])['r']
    if r < 0.4:
        # plant_pink
        h = _BAKED_CREATE_PETAL_MATERIAL.get(seed % 60, _BAKED_CREATE_PETAL_MATERIAL[0])['h']
        s = _BAKED_CREATE_PETAL_MATERIAL.get(seed % 60, _BAKED_CREATE_PETAL_MATERIAL[0])['s']
        v = _BAKED_CREATE_PETAL_MATERIAL.get(seed % 60, _BAKED_CREATE_PETAL_MATERIAL[0])['v']
    elif r < 0.6:
        # plant_white
        h = _BAKED_CREATE_PETAL_MATERIAL.get(seed % 60, _BAKED_CREATE_PETAL_MATERIAL[0])['h']
        s = _BAKED_CREATE_PETAL_MATERIAL.get(seed % 60, _BAKED_CREATE_PETAL_MATERIAL[0])['s']
        v = _BAKED_CREATE_PETAL_MATERIAL.get(seed % 60, _BAKED_CREATE_PETAL_MATERIAL[0])['v']
    elif r < 0.8:
        # plant_red
        h = _BAKED_CREATE_PETAL_MATERIAL.get(seed % 60, _BAKED_CREATE_PETAL_MATERIAL[0])['h']
        s = _BAKED_CREATE_PETAL_MATERIAL.get(seed % 60, _BAKED_CREATE_PETAL_MATERIAL[0])['s']
        v = _BAKED_CREATE_PETAL_MATERIAL.get(seed % 60, _BAKED_CREATE_PETAL_MATERIAL[0])['v']
    else:
        # plant_yellow
        h = _BAKED_CREATE_PETAL_MATERIAL.get(seed % 60, _BAKED_CREATE_PETAL_MATERIAL[0])['h']
        s = _BAKED_CREATE_PETAL_MATERIAL.get(seed % 60, _BAKED_CREATE_PETAL_MATERIAL[0])['s']
        v = _BAKED_CREATE_PETAL_MATERIAL.get(seed % 60, _BAKED_CREATE_PETAL_MATERIAL[0])['v']

    petal_rgba = _hsv2rgba(h, s, v)

    mat = _new_mat("PetalMaterial")
    nt = mat.node_tree
    N = nt.nodes
    L = nt.links

    out = N.new('ShaderNodeOutputMaterial')

    petal_col = N.new('ShaderNodeRGB')
    petal_col.outputs[0].default_value = petal_rgba

    trans = N.new('ShaderNodeBsdfTranslucent')
    L.new(petal_col.outputs[0], trans.inputs['Color'])

    specular = float(np.clip(np.random.normal(0.6, 0.1), 0, 1))
    roughness = float(np.clip(np.random.normal(0.4, 0.05), 0, 1))
    translucent_amt = float(np.clip(np.random.normal(0.3, 0.05), 0, 1))

    bsdf = N.new('ShaderNodeBsdfPrincipled')
    L.new(petal_col.outputs[0], bsdf.inputs['Base Color'])
    bsdf.inputs['Specular IOR Level'].default_value = specular
    bsdf.inputs['Roughness'].default_value = roughness

    mix_sh = N.new('ShaderNodeMixShader')
    mix_sh.inputs['Fac'].default_value = translucent_amt
    L.new(bsdf.outputs[0], mix_sh.inputs[1])
    L.new(trans.outputs[0], mix_sh.inputs[2])

    L.new(mix_sh.outputs[0], out.inputs['Surface'])

    return mat


def create_flower_center_material(seed):

    mat = _new_mat("FlowerCenterMaterial")
    nt = mat.node_tree
    N = nt.nodes
    L = nt.links

    out = N.new('ShaderNodeOutputMaterial')

    ao = N.new('ShaderNodeAmbientOcclusion')

    cr = N.new('ShaderNodeValToRGB')
    cr.color_ramp.elements.new(1)
    cr.color_ramp.elements[0].position = 0.484
    cr.color_ramp.elements[0].color = (0.0127, 0.0075, 0.0026, 1.0)
    cr.color_ramp.elements[1].position = 0.859
    cr.color_ramp.elements[1].color = (0.0848, 0.0066, 0.0007, 1.0)
    cr.color_ramp.elements[2].position = 1.0
    cr.color_ramp.elements[2].color = (1.0, 0.6228, 0.1069, 1.0)
    L.new(ao.outputs['Color'], cr.inputs['Fac'])

    bsdf = N.new('ShaderNodeBsdfPrincipled')
    L.new(cr.outputs['Color'], bsdf.inputs['Base Color'])
    L.new(bsdf.outputs[0], out.inputs[0])

    return mat


# ═══════════════════════════════════════════════════════════════════════════════
# Scene setup
# ═══════════════════════════════════════════════════════════════════════════════

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes): bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves): bpy.data.curves.remove(c)
    for mt in list(bpy.data.materials): bpy.data.materials.remove(mt)
    for ng in list(bpy.data.node_groups): bpy.data.node_groups.remove(ng)
    for col in list(bpy.data.collections): bpy.data.collections.remove(col)
    bpy.context.scene.cursor.location = (0, 0, 0)


# ═══════════════════════════════════════════════════════════════════════════════
# Space colonization tree skeleton
# ═══════════════════════════════════════════════════════════════════════════════

class TreeVertices:
    def __init__(self, vtxs=None, parent=None, level=None):
        if vtxs is None: vtxs = np.array([[0, 0, 0]], dtype=float)
        elif isinstance(vtxs, list): vtxs = np.array(vtxs, dtype=float)
        parent = [-1] * len(vtxs) if parent is None else parent
        level = [0] * len(vtxs) if level is None else level
        self.vtxs = vtxs; self.parent = parent; self.level = level

    def get_idxs(self): return list(np.arange(len(self.vtxs)))

    def get_edges(self):
        edges = np.stack([np.arange(len(self.vtxs)), np.array(self.parent)], 1)
        return edges[edges[:, 1] != -1]

    def append(self, v, p, l=None):
        self.vtxs = np.append(self.vtxs, v, axis=0)
        self.parent += p
        if l is None: l = [0] * len(v)
        elif isinstance(l, int): l = [l] * len(v)
        self.level += l

    def __len__(self): return len(self.vtxs)


def rodrigues_rot(v, k, theta):
    k, v = np.array(k, dtype=float), np.array(v, dtype=float)
    kn = np.linalg.norm(k)
    if kn < 1e-10: return v
    k = k / kn
    return v * math.cos(theta) + np.cross(k, v) * math.sin(theta) + k * np.dot(k, v) * (1 - math.cos(theta))


def rand_path(n_pts, sz=1, std=0.3, momentum=0.5, init_vec=None, init_pt=None,
              pull_dir=None, pull_init=1, pull_factor=0, sz_decay=1, decay_mom=True):
    if init_vec is None: init_vec = [0, 0, 1]
    if init_pt is None: init_pt = [0, 0, 0]
    init_vec, init_pt = np.array(init_vec, dtype=float), np.array(init_pt, dtype=float)
    if pull_dir is not None:
        pull_dir = np.array(pull_dir, dtype=float)
        init_vec = init_vec + pull_init * pull_dir
    norm = np.linalg.norm(init_vec)
    if norm > 1e-10: init_vec /= norm
    path = np.zeros((n_pts, 3)); path[0] = init_pt
    for i in range(1, n_pts):
        prev_delta = init_vec * sz if i == 1 else path[i-1] - path[i-2]
        prev_sz = np.linalg.norm(prev_delta)
        new_delta = prev_delta + np.random.normal(0, 1) * std
        if pull_dir is not None: new_delta += pull_factor * pull_dir
        nd = np.linalg.norm(new_delta)
        if nd > 1e-10: new_delta = (new_delta / nd) * prev_sz
        mom = 1 - (1 - momentum) * (i + 1) / n_pts if decay_mom else momentum
        delta = prev_delta * mom + new_delta * (1 - mom)
        dn = np.linalg.norm(delta)
        if dn > 1e-10: delta = (delta / dn) * sz * (sz_decay ** i)
        path[i] = path[i-1] + delta
    return path


def get_spawn_pt(path, rng=None, ang_min=math.pi/6, ang_max=0.9*math.pi/2,
                 rnd_idx=None, ang_sign=None, axis2=None, init_vec=None, z_bias=0):
    if rng is None: rng = [0.5, 1]
    n = len(path)
    if n == 1: return 0, path[0], init_vec if init_vec is not None else np.array([0, 0, 1])
    if rnd_idx is None: rnd_idx = 0.0
    rnd_idx = max(1, min(rnd_idx, n - 1))
    if init_vec is None:
        curr_vec = path[rnd_idx] - path[rnd_idx - 1]
        axis1 = np.array([curr_vec[1], -curr_vec[0], 0])
        if axis2 is None: axis2 = rodrigues_rot(curr_vec, axis1, math.pi / 2)
        if callable(axis2): axis2 = axis2()
        rnd_ang = np.random.uniform(0, 1) * (ang_max - ang_min) + ang_min
        if ang_sign is None: ang_sign = np.sign(np.random.normal(0, 1))
        rnd_ang *= ang_sign
        init_vec = rodrigues_rot(curr_vec, axis2, rnd_ang)
    return rnd_idx, path[rnd_idx], init_vec


def recursive_path(tree, parent_idxs, level, path_kargs=None, spawn_kargs=None,
                   n=1, symmetry=False, children=None):
    if path_kargs is None: return
    if symmetry: n = 2 * n
    for bi in range(n):
        ci = bi // 2 if symmetry else bi
        cp, cs = path_kargs(ci), spawn_kargs(ci)
        if symmetry: cs["ang_sign"] = 2 * (bi % 2) - 1
        pidx, ipt, ivec = get_spawn_pt(tree.vtxs[parent_idxs], **cs)
        pidx = parent_idxs[pidx]
        path = rand_path(**cp, init_pt=ipt, init_vec=ivec)
        new_vtxs = path[1:]
        new_idxs = list(np.arange(len(new_vtxs)) + len(tree))
        node_idxs = [pidx] + new_idxs
        tree.append(new_vtxs, node_idxs[:-1], level)
        if children:
            for c in children:
                recursive_path(tree, node_idxs, level + 1, **c)


def compute_dists(atts, vtxs):
    diff = atts[:, None, :] - vtxs[None, :, :]
    return np.linalg.norm(diff, axis=2), diff


def space_colonization(tree, atts, D=0.1, d=10.0, s=0.1, pull_dir=None,
                       dir_rand=0.1, mag_rand=0.15, n_steps=200, level=0):
    if callable(atts): atts = atts(tree.vtxs)
    curr_min = np.zeros(len(atts)) + d
    curr_match = -np.ones(len(atts), dtype=int)
    dists, deltas = compute_dists(atts, tree.vtxs)
    min_dist, closest = dists.min(1), dists.argmin(1)
    keep = min_dist > s
    atts, deltas, curr_min, curr_match = atts[keep], deltas[keep], curr_min[keep], curr_match[keep]
    min_dist, closest = min_dist[keep], closest[keep]
    upd = min_dist < curr_min
    curr_min[upd], curr_match[upd] = min_dist[upd], closest[upd]
    if np.all(curr_match == -1): return
    for _ in range(n_steps):
        new_vtxs, new_parents = [], []
        for n_idx in np.unique(curr_match):
            if n_idx == -1: continue
            md = deltas[curr_match == n_idx]
            norms = np.maximum(np.linalg.norm(md[:, n_idx, :], axis=1, keepdims=True), 1e-10)
            new_dir = (md[:, n_idx, :] / norms).mean(0)
            nd = np.linalg.norm(new_dir)
            if nd > 1e-10: new_dir /= nd
            if pull_dir is not None:
                new_dir += np.array(pull_dir)
                nd = np.linalg.norm(new_dir)
                if nd > 1e-10: new_dir /= nd
            new_dir += np.random.normal(0, 1) * dir_rand
            tmp_D = D * np.exp(np.random.normal(0, 1) * mag_rand)
            new_vtxs.append(tree.vtxs[n_idx] + tmp_D * new_dir)
            new_parents.append(n_idx)
        if not new_vtxs: break
        off = len(tree)
        new_vtxs = np.stack(new_vtxs, 0)
        tree.append(new_vtxs, new_parents, level)
        dn, dd = compute_dists(atts, new_vtxs)
        deltas = np.concatenate([deltas, dd], axis=1)
        md_new, cl_new = dn.min(1), dn.argmin(1) + off
        keep = md_new > s
        atts, deltas, curr_min, curr_match = atts[keep], deltas[keep], curr_min[keep], curr_match[keep]
        md_new, cl_new = md_new[keep], cl_new[keep]
        upd = md_new < curr_min
        curr_min[upd], curr_match[upd] = md_new[upd], cl_new[upd]
        if len(atts) == 0: break


# ═══════════════════════════════════════════════════════════════════════════════
# Tree attribute parsing
# ═══════════════════════════════════════════════════════════════════════════════

def dfs_tree(idx, edge_ref, parents, depth, rev_depth, n_leaves, child_idx):
    children = [v for v in edge_ref[idx] if v != parents[idx]]
    if not children:
        curr_idx, curr_depth = idx, 0
        child_idx[curr_idx] = -1
        while curr_idx != 0:
            prev_idx = curr_idx; curr_idx = parents[curr_idx]; curr_depth += 1
            n_leaves[curr_idx] += 1
            if rev_depth[curr_idx] < curr_depth:
                child_idx[curr_idx] = prev_idx; rev_depth[curr_idx] = curr_depth
    else:
        for c in children:
            parents[c] = idx; depth[c] = depth[idx] + 1
            dfs_tree(c, edge_ref, parents, depth, rev_depth, n_leaves, child_idx)


def parse_tree_attributes(vtx):
    sys.setrecursionlimit(10000)
    n = len(vtx.vtxs)
    parents, depth, rev_depth = np.zeros(n, dtype=int), np.zeros(n, dtype=int), np.zeros(n, dtype=int)
    n_leaves, child_idx_arr = np.zeros(n, dtype=int), np.zeros(n, dtype=int)
    edge_ref = {i: [] for i in range(n)}
    for e in vtx.get_edges():
        edge_ref[e[0]].append(e[1]); edge_ref[e[1]].append(e[0])
    dfs_tree(0, edge_ref, parents, depth, rev_depth, n_leaves, child_idx_arr)
    return rev_depth


# ═══════════════════════════════════════════════════════════════════════════════
# Attractor point sampling
# ═══════════════════════════════════════════════════════════════════════════════

def get_pts_sphere(n, radius, offset):
    pts = np.random.randn(n * 3, 3)
    norms = np.linalg.norm(pts, axis=1)
    pts = pts[norms > 1e-10][:n]
    pts = pts / np.linalg.norm(pts, axis=1, keepdims=True)
    r = np.random.rand(len(pts)) ** (1.0 / 3.0)
    pts = pts * (r * radius)[:, np.newaxis] + np.array(offset)
    return pts


def get_pts_cone_blender(n, sx, sy, sz, offset):
    """Sample n points inside a Blender cone primitive volume."""

    offset = np.array(offset)
    pts = []
    while len(pts) < n:
        z_local = np.random.uniform(-sz, sz)
        frac = (sz - z_local) / (2 * sz)
        rx, ry = sx * frac, sy * frac
        angle = np.random.uniform(0, 2 * math.pi)
        r_norm = np.sqrt(np.random.uniform(0, 1))
        x = rx * r_norm * math.cos(angle)
        y = ry * r_norm * math.sin(angle)
        pts.append([x + offset[0], y + offset[1], z_local + offset[2]])
    return np.array(pts[:n])


# ═══════════════════════════════════════════════════════════════════════════════
# Skeleton mesh creation (separate from skinning)
# ═══════════════════════════════════════════════════════════════════════════════

def create_skeleton_mesh(vtx, rev_depth, scale=0.2):
    """Create a Blender mesh object from tree skeleton with rev_depth attribute."""

    verts = vtx.vtxs * scale
    edges = vtx.get_edges()
    mesh_data = bpy.data.meshes.new("BushSkeleton")
    mesh_data.from_pydata(verts.tolist(), edges.tolist(), [])
    mesh_data.update()
    obj = bpy.data.objects.new("BushSkeleton", mesh_data)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    attr = mesh_data.attributes.new(name="rev_depth", type="INT", domain="POINT")
    attr.data.foreach_set("value", rev_depth.astype(int))
    return obj


# ═══════════════════════════════════════════════════════════════════════════════
# Skeleton to tube mesh (GeoNodes skinning with Bezier smoothing)
# ═══════════════════════════════════════════════════════════════════════════════

def skeleton_to_mesh(skel_obj, min_radius=0.005, max_radius=0.025, exponent=2, profile_res=16):
    """Clone skeleton, skin into tubes via GeoNodes, return tube mesh object."""

    mesh_copy = skel_obj.data.copy()
    tube_obj = bpy.data.objects.new("BushTubes", mesh_copy)
    bpy.context.scene.collection.objects.link(tube_obj)
    bpy.context.view_layer.objects.active = tube_obj

    ng = bpy.data.node_groups.new("SkinBush", 'GeometryNodeTree')
    in_s = ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.move(in_s, 0)
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')

    # MeshToCurve
    m2c = N.new('GeometryNodeMeshToCurve')
    L.new(gi.outputs['Geometry'], m2c.inputs['Mesh'])

    sst = N.new('GeometryNodeCurveSplineType'); sst.spline_type = 'BEZIER'
    L.new(m2c.outputs['Curve'], sst.inputs['Curve'])
    sht = N.new('GeometryNodeCurveSetHandles'); sht.handle_type = 'AUTO'
    L.new(sst.outputs['Curve'], sht.inputs['Curve'])
    pos = N.new('GeometryNodeInputPosition')
    noise = N.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 1.0
    L.new(pos.outputs['Position'], noise.inputs['Vector'])
    sc = N.new('ShaderNodeVectorMath'); sc.operation = 'SCALE'
    L.new(noise.outputs['Color'], sc.inputs[0]); sc.inputs['Scale'].default_value = 0.02
    shp = N.new('GeometryNodeSetCurveHandlePositions')
    L.new(sht.outputs['Curve'], shp.inputs['Curve'])
    L.new(sc.outputs['Vector'], shp.inputs['Offset'])

    # Radius: (rev_depth * 0.1 * 0.1) ^ exponent, clamped
    na = N.new('GeometryNodeInputNamedAttribute'); na.data_type = 'INT'
    na.inputs['Name'].default_value = "rev_depth"
    mul1 = N.new('ShaderNodeMath'); mul1.operation = 'MULTIPLY'
    L.new(na.outputs[0], mul1.inputs[0]); mul1.inputs[1].default_value = 0.10
    mul2 = N.new('ShaderNodeMath'); mul2.operation = 'MULTIPLY'
    L.new(mul1.outputs[0], mul2.inputs[0]); mul2.inputs[1].default_value = 0.1
    pw = N.new('ShaderNodeMath'); pw.operation = 'POWER'
    L.new(mul2.outputs[0], pw.inputs[0]); pw.inputs[1].default_value = exponent
    mx = N.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'
    L.new(pw.outputs[0], mx.inputs[0]); mx.inputs[1].default_value = min_radius
    mn = N.new('ShaderNodeMath'); mn.operation = 'MINIMUM'
    L.new(mx.outputs[0], mn.inputs[0]); mn.inputs[1].default_value = max_radius

    scr = N.new('GeometryNodeSetCurveRadius')
    L.new(shp.outputs['Curve'], scr.inputs['Curve'])
    L.new(mn.outputs[0], scr.inputs['Radius'])

    cc = N.new('GeometryNodeCurvePrimitiveCircle')
    cc.inputs['Resolution'].default_value = profile_res; cc.inputs['Radius'].default_value = 1.0
    c2m = N.new('GeometryNodeCurveToMesh')
    L.new(scr.outputs['Curve'], c2m.inputs['Curve'])
    L.new(cc.outputs['Curve'], c2m.inputs['Profile Curve'])
    L.new(mn.outputs[0], c2m.inputs['Scale'])
    c2m.inputs['Fill Caps'].default_value = True

    mbd = N.new('GeometryNodeMergeByDistance')
    L.new(c2m.outputs['Mesh'], mbd.inputs['Geometry'])
    mbd.inputs['Distance'].default_value = 0.001
    L.new(mbd.outputs['Geometry'], go.inputs['Geometry'])

    mod = tube_obj.modifiers.new("Skin", 'NODES'); mod.node_group = ng
    bpy.ops.object.select_all(action="DESELECT")
    tube_obj.select_set(True); bpy.context.view_layer.objects.active = tube_obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return tube_obj


# ═══════════════════════════════════════════════════════════════════════════════
# Twig generation (matching shrubtwig_config + subtwig_config)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_twig_mesh(child_col, bark_mat, scale=0.2):
    """Generate one twig mesh with children: skeleton -> skin + child instancing -> join.
    Bark material applied to twig tubes."""

    subtwig_config = {
        "n": 3, "symmetry": True,
        "path_kargs": lambda idx: {"n_pts": 3, "std": 1, "momentum": 1, "sz": 0.6 - 0.1 * idx},
        "spawn_kargs": lambda idx: {
            "rng": [0.2, 0.9], "z_bias": 0.1, "rnd_idx": 2 * idx + 1,
            "ang_min": math.pi / 4, "ang_max": math.pi / 4 + math.pi / 16, "axis2": [0, 0, 1],
        },
        "children": [],
    }
    shrubtwig_config = {
        "n": 1,
        "path_kargs": lambda idx: {"n_pts": 6, "sz": 0.5, "std": 0.5, "momentum": 0.7},
        "spawn_kargs": lambda idx: {"init_vec": [0, 1, 0]},
        "children": [subtwig_config],
    }
    vtx = TreeVertices(np.array([[0.0, 0.0, 0.0]]))
    recursive_path(vtx, vtx.get_idxs(), level=0, **shrubtwig_config)
    rev_depth = parse_tree_attributes(vtx)
    verts = vtx.vtxs * scale
    edges = vtx.get_edges()

    # ── Create skeleton mesh (for child instancing) ──
    me_skel = bpy.data.meshes.new("TwigSkel")
    me_skel.from_pydata(verts.tolist(), edges.tolist(), [])
    me_skel.update()
    skel_obj = bpy.data.objects.new("TwigSkel", me_skel)
    bpy.context.scene.collection.objects.link(skel_obj)

    # ── Instance children on skeleton (GeoNodes-based, matching twig child_placement) ──
    add_children_to_twig(skel_obj, child_col, density=0.7, min_scale=0.4, max_scale=0.6, multi_inst=2)

    # ── Clone skeleton for skinning ──
    me_skin = bpy.data.meshes.new("TwigSkinSkel")
    me_skin.from_pydata(verts.tolist(), edges.tolist(), [])
    me_skin.update()
    skin_obj = bpy.data.objects.new("TwigSkin", me_skin)
    bpy.context.scene.collection.objects.link(skin_obj)
    attr = me_skin.attributes.new(name="rev_depth", type="INT", domain="POINT")
    attr.data.foreach_set("value", rev_depth.astype(int))

    # ── Skin skeleton clone into tubes ──
    ng = bpy.data.node_groups.new("SkinTwig", 'GeometryNodeTree')
    in_s = ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.move(in_s, 0)
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')
    m2c = N.new('GeometryNodeMeshToCurve')
    L.new(gi.outputs['Geometry'], m2c.inputs['Mesh'])
    sst = N.new('GeometryNodeCurveSplineType'); sst.spline_type = 'BEZIER'
    L.new(m2c.outputs['Curve'], sst.inputs['Curve'])
    sht = N.new('GeometryNodeCurveSetHandles'); sht.handle_type = 'AUTO'
    L.new(sst.outputs['Curve'], sht.inputs['Curve'])
    na = N.new('GeometryNodeInputNamedAttribute'); na.data_type = 'INT'
    na.inputs['Name'].default_value = "rev_depth"
    mul1 = N.new('ShaderNodeMath'); mul1.operation = 'MULTIPLY'
    L.new(na.outputs[0], mul1.inputs[0]); mul1.inputs[1].default_value = 0.10
    mul2 = N.new('ShaderNodeMath'); mul2.operation = 'MULTIPLY'
    L.new(mul1.outputs[0], mul2.inputs[0]); mul2.inputs[1].default_value = 0.1
    pw = N.new('ShaderNodeMath'); pw.operation = 'POWER'
    L.new(mul2.outputs[0], pw.inputs[0]); pw.inputs[1].default_value = 1.5
    mx = N.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'
    L.new(pw.outputs[0], mx.inputs[0]); mx.inputs[1].default_value = 0.02
    mn = N.new('ShaderNodeMath'); mn.operation = 'MINIMUM'
    L.new(mx.outputs[0], mn.inputs[0]); mn.inputs[1].default_value = 0.1
    scr = N.new('GeometryNodeSetCurveRadius')
    L.new(sht.outputs['Curve'], scr.inputs['Curve']); L.new(mn.outputs[0], scr.inputs['Radius'])
    cc = N.new('GeometryNodeCurvePrimitiveCircle')
    cc.inputs['Resolution'].default_value = 20; cc.inputs['Radius'].default_value = 1.0
    c2m = N.new('GeometryNodeCurveToMesh')
    L.new(scr.outputs['Curve'], c2m.inputs['Curve'])
    L.new(cc.outputs['Curve'], c2m.inputs['Profile Curve'])
    L.new(mn.outputs[0], c2m.inputs['Scale'])
    c2m.inputs['Fill Caps'].default_value = True
    mbd = N.new('GeometryNodeMergeByDistance')
    L.new(c2m.outputs['Mesh'], mbd.inputs['Geometry']); mbd.inputs['Distance'].default_value = 0.001
    L.new(mbd.outputs['Geometry'], go.inputs['Geometry'])
    mod = skin_obj.modifiers.new("Skin", 'NODES'); mod.node_group = ng
    bpy.ops.object.select_all(action="DESELECT")
    skin_obj.select_set(True); bpy.context.view_layer.objects.active = skin_obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # ── Apply bark material to twig tube mesh ──
    skin_obj.data.materials.clear()
    skin_obj.data.materials.append(bark_mat)

    # ── Join tube + children ──
    bpy.ops.object.select_all(action="DESELECT")
    skel_obj.select_set(True); skin_obj.select_set(True)
    bpy.context.view_layer.objects.active = skin_obj
    bpy.ops.object.join()
    result = bpy.context.active_object
    return result


def _make_leaf_mesh(name, leaf_width, leaf_height, jigsaw_depth=1.0, n_subdiv_x=12, n_subdiv_y=20):
    bm = bmesh.new()
    # 1. Subdivided plane
    hw, hh = leaf_width / 2, leaf_height / 2
    for iy in range(n_subdiv_y + 1):
        for ix in range(n_subdiv_x + 1):
            x = -hw + ix * leaf_width / n_subdiv_x
            y = -hh + iy * leaf_height / n_subdiv_y
            bm.verts.new((x, y, 0))
    bm.verts.ensure_lookup_table()
    for iy in range(n_subdiv_y):
        for ix in range(n_subdiv_x):
            i00 = iy * (n_subdiv_x + 1) + ix
            i10 = i00 + 1
            i01 = i00 + (n_subdiv_x + 1)
            i11 = i01 + 1
            bm.faces.new([bm.verts[i00], bm.verts[i10], bm.verts[i11], bm.verts[i01]])
    # 2. Leaf shape outline: elliptical with pointed tips
    def leaf_shape(x, y):
        t = (y + hh) / leaf_height
        w_frac = math.sin(t * math.pi) ** 0.7 * (1 - (2 * t - 1) ** 6) ** 0.3
        max_x = hw * w_frac
        return abs(x) - max_x
    # 3. Serrated edge (jigsaw pattern)
    def jigsaw(y):
        freq = 18.0
        return math.sin(y * freq * math.pi / leaf_height) * jigsaw_depth * 0.008
    # 4. Delete faces outside outline
    faces_to_del = []
    for f in bm.faces:
        cx = sum(v.co.x for v in f.verts) / len(f.verts)
        cy = sum(v.co.y for v in f.verts) / len(f.verts)
        dist = leaf_shape(cx, cy) + jigsaw(cy)
        if dist > 0:
            faces_to_del.append(f)
    bmesh.ops.delete(bm, geom=faces_to_del, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    # 5. Midrib Z-displacement + vein pattern
    for v in bm.verts:
        t = (v.co.y + hh) / leaf_height
        midrib_z = 0.003 * math.exp(-abs(v.co.x) / (hw * 0.15))
        vein_angle = 0.8
        vein_density = 12.0
        vein_x = abs(v.co.x) / hw if hw > 1e-6 else 0
        vein_y = t * vein_density
        vein_z = 0.001 * math.sin(vein_y * math.pi) * (1 - vein_x) * math.exp(-vein_x * 2)
        v.co.z += midrib_z + vein_z
    # 6. Wave deformation
    for v in bm.verts:
        t = (v.co.y + hh) / leaf_height
        v.co.z += 0.008 * math.sin(t * 2 * math.pi) * (1 - abs(v.co.x) / hw)
        v.co.z += 0.003 * math.sin(abs(v.co.x) / hw * math.pi)
    # 7. Rotate to XZ plane
    for v in bm.verts:
        v.co.x, v.co.y, v.co.z = v.co.x, -v.co.z, v.co.y
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return me


def _make_flower_mesh(name, flower_rad=0.2, n_petals=None, curl_deg=30, petal_res_h=4, petal_res_v=3):
    if n_petals is None:
        n_petals = np.random.randint(5, 12)
    pct_inner = np.random.uniform(0.1, 0.35)
    center_rad = flower_rad * pct_inner
    petal_length = flower_rad * (1 - pct_inner)
    base_width = 2 * math.pi * center_rad / max(n_petals * 0.8, 1)
    top_width = base_width * np.random.uniform(0.3, 1.2)
    curl_rad = math.radians(curl_deg)
    wrinkle = np.random.uniform(0.002, 0.01)
    min_angle = math.radians(np.random.uniform(-10, 40))
    max_angle = math.radians(np.random.uniform(50, 90))

    bm = bmesh.new()

    # 1. Center disc (flattened sphere)
    bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=8, radius=center_rad)
    for v in bm.verts:
        v.co.z *= 0.08

    # Tag center verts so we can assign material later
    center_vert_count = len(bm.verts)

    # 2. Create petals
    for pi in range(n_petals):
        angle = 2 * math.pi * pi / n_petals + np.random.uniform(-0.1, 0.1)
        petal_angle = np.random.uniform(min_angle, max_angle)

        petal_verts = []
        for iy in range(petal_res_v + 1):
            t = iy / petal_res_v
            w = base_width * (1 - t) + top_width * t
            w *= math.sin(max(t, 0.05) * math.pi) ** 0.4
            for ix in range(petal_res_h + 1):
                s = ix / petal_res_h - 0.5
                px = s * w
                py = t * petal_length
                pz = wrinkle * math.sin(s * 4 * math.pi) * t
                curl_angle = petal_angle + curl_rad * t
                py_curled = py * math.cos(curl_angle)
                pz_curled = py * math.sin(curl_angle) + pz
                wx = px * math.cos(angle) - (center_rad + py_curled) * math.sin(angle)
                wy = px * math.sin(angle) + (center_rad + py_curled) * math.cos(angle)
                wz = pz_curled
                petal_verts.append(bm.verts.new((wx, wy, wz)))

        bm.verts.ensure_lookup_table()
        for iy in range(petal_res_v):
            for ix in range(petal_res_h):
                stride = petal_res_h + 1
                i0 = petal_verts[iy * stride + ix]
                i1 = petal_verts[iy * stride + ix + 1]
                i2 = petal_verts[(iy + 1) * stride + ix + 1]
                i3 = petal_verts[(iy + 1) * stride + ix]
                try:
                    bm.faces.new([i0, i1, i2, i3])
                except ValueError:
                    pass

    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return me, center_vert_count


def create_child_collection(scale=0.35, leaf_mat=None, petal_mat=None, center_mat=None):
    """Create leaf or flower collection with materials assigned."""

    col = bpy.data.collections.new("BushChildren")
    bpy.context.scene.collection.children.link(col)

    if LEAF_TYPE == 1:  # leaf_v2
        leaf_width_base = np.random.rand() * 0.15 + 0.05
        for i in range(3):
            w = leaf_width_base * np.random.uniform(0.8, 1.2)
            h = w * np.random.uniform(2.0, 3.0)
            jigsaw = np.random.uniform(0.5, 2.0)
            me = _make_leaf_mesh(f"leaf_{i}", w, h, jigsaw_depth=jigsaw, n_subdiv_x=8, n_subdiv_y=14)
            obj = bpy.data.objects.new(f"leaf_{i}", me)
            # Assign leaf material
            if leaf_mat is not None:
                obj.data.materials.append(leaf_mat)
            bpy.context.scene.collection.objects.link(obj)
            bpy.context.scene.collection.objects.unlink(obj)
            col.objects.link(obj)
    else:  # flower
        flower_rad_base = np.random.uniform(0.04, 0.10)
        for i in range(3):
            rad = flower_rad_base * np.random.uniform(0.85, 1.15)
            curl = np.random.normal(30, 15)
            me, center_vert_count = _make_flower_mesh(f"flower_{i}", flower_rad=rad, curl_deg=curl)
            obj = bpy.data.objects.new(f"flower_{i}", me)
            # Assign petal + center materials via material slots
            if petal_mat is not None:
                obj.data.materials.append(petal_mat)      # slot 0 = petal (default)
            if center_mat is not None:
                obj.data.materials.append(center_mat)      # slot 1 = center
                # Assign center material to center faces
                bm = bmesh.new()
                bm.from_mesh(me)
                bm.faces.ensure_lookup_table()
                bm.verts.ensure_lookup_table()
                center_vert_indices = set(range(center_vert_count))
                for f in bm.faces:
                    if all(v.index in center_vert_indices for v in f.verts):
                        f.material_index = 1
                bm.to_mesh(me)
                bm.free()
            bpy.context.scene.collection.objects.link(obj)
            bpy.context.scene.collection.objects.unlink(obj)
            col.objects.link(obj)
    return col


def add_children_to_twig(twig_skel_obj, child_col, density=1.0, min_scale=0.4, max_scale=0.6, multi_inst=2):
    """Instance child collection (leaves/flowers) on twig skeleton via GeoNodes coll_distribute."""

    ng = bpy.data.node_groups.new("TwigChildren", 'GeometryNodeTree')
    in_s = ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.move(in_s, 0)
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')

    m2c = N.new('GeometryNodeMeshToCurve')
    L.new(gi.outputs['Geometry'], m2c.inputs['Mesh'])
    c2p = N.new('GeometryNodeCurveToPoints')
    c2p.inputs['Count'].default_value = multi_inst
    L.new(m2c.outputs['Curve'], c2p.inputs['Curve'])

    rv = N.new('FunctionNodeRandomValue')
    lt = N.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'
    L.new(rv.outputs[1], lt.inputs[0]); lt.inputs[1].default_value = density

    rv_p = N.new('FunctionNodeRandomValue')
    rv_p.inputs[2].default_value = -1.5; rv_p.inputs[3].default_value = 1.5
    rv_y = N.new('FunctionNodeRandomValue')
    rv_y.inputs[2].default_value = -3.14; rv_y.inputs[3].default_value = 3.14
    comb = N.new('ShaderNodeCombineXYZ')
    L.new(rv_p.outputs[1], comb.inputs['X']); L.new(rv_y.outputs[1], comb.inputs['Z'])

    rv_sc = N.new('FunctionNodeRandomValue')
    rv_sc.inputs[2].default_value = min_scale; rv_sc.inputs[3].default_value = max_scale

    ci = N.new('GeometryNodeCollectionInfo')
    ci.inputs['Collection'].default_value = child_col
    ci.inputs['Separate Children'].default_value = True
    ci.inputs['Reset Children'].default_value = True

    iop = N.new('GeometryNodeInstanceOnPoints')
    L.new(c2p.outputs['Points'], iop.inputs['Points'])
    L.new(lt.outputs[0], iop.inputs['Selection'])
    L.new(ci.outputs['Instances'], iop.inputs['Instance'])
    iop.inputs['Pick Instance'].default_value = True
    L.new(comb.outputs['Vector'], iop.inputs['Rotation'])
    L.new(rv_sc.outputs[1], iop.inputs['Scale'])

    ri = N.new('GeometryNodeRealizeInstances')
    L.new(iop.outputs['Instances'], ri.inputs['Geometry'])
    L.new(ri.outputs['Geometry'], go.inputs['Geometry'])

    mod = twig_skel_obj.modifiers.new("Children", 'NODES'); mod.node_group = ng
    bpy.ops.object.select_all(action="DESELECT")
    twig_skel_obj.select_set(True); bpy.context.view_layer.objects.active = twig_skel_obj
    bpy.ops.object.modifier_apply(modifier=mod.name)


def make_twig_collection(n_twigs=3, scale=0.2, bark_mat=None):
    """Generate n_twigs twig mesh variants with children (leaves/flowers) in a Blender Collection."""

    child_col = create_child_collection(scale,
                                         leaf_mat=LEAF_MAT if LEAF_TYPE == 1 else None,
                                         petal_mat=PETAL_MAT if LEAF_TYPE == 0 else None,
                                         center_mat=CENTER_MAT if LEAF_TYPE == 0 else None)
    col = bpy.data.collections.new("BushTwigs")
    bpy.context.scene.collection.children.link(col)
    for i in range(n_twigs):
        twig = generate_twig_mesh(child_col, bark_mat=bark_mat, scale=scale)
        twig.name = f"twig_{i}"
        bpy.context.scene.collection.objects.unlink(twig)
        col.objects.link(twig)
    # Cleanup child collection
    for o in list(child_col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(child_col)
    return col


# ═══════════════════════════════════════════════════════════════════════════════
# Twig distribution GeoNodes (matching coll_distribute)
# ═══════════════════════════════════════════════════════════════════════════════

def build_coll_distribute(skel_obj, twig_col, depth_range=(0, 2.7), density=0.7,
                          multi_inst=3, min_scale=0.24, max_scale=0.28,
                          pitch_offset=1.0, pitch_variance=2.0, yaw_variance=2.0):
    """Add GeoNodes modifier that instances twigs from collection onto skeleton."""

    ng = bpy.data.node_groups.new("DistTwigs", 'GeometryNodeTree')
    in_s = ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.move(in_s, 0)
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')

    na = N.new('GeometryNodeInputNamedAttribute'); na.data_type = 'INT'
    na.inputs['Name'].default_value = "rev_depth"
    gt = N.new('FunctionNodeCompare'); gt.data_type = 'FLOAT'
    L.new(na.outputs[0], gt.inputs[0]); gt.inputs[1].default_value = depth_range[0] - 0.01
    lt = N.new('FunctionNodeCompare'); lt.data_type = 'FLOAT'; lt.operation = 'LESS_THAN'
    L.new(na.outputs[0], lt.inputs[0]); lt.inputs[1].default_value = depth_range[1] + 0.01
    sel_and = N.new('FunctionNodeBooleanMath')
    L.new(gt.outputs[0], sel_and.inputs[0]); L.new(lt.outputs[0], sel_and.inputs[1])

    m2c = N.new('GeometryNodeMeshToCurve')
    L.new(gi.outputs['Geometry'], m2c.inputs['Mesh'])
    L.new(sel_and.outputs[0], m2c.inputs['Selection'])

    c2p = N.new('GeometryNodeCurveToPoints')
    c2p.inputs['Count'].default_value = multi_inst
    L.new(m2c.outputs['Curve'], c2p.inputs['Curve'])

    m2p = N.new('GeometryNodeMeshToPoints')
    L.new(gi.outputs['Geometry'], m2p.inputs['Mesh'])
    L.new(sel_and.outputs[0], m2p.inputs['Selection'])

    pos_in = N.new('GeometryNodeInputPosition')
    sn = N.new('GeometryNodeSampleNearest')
    L.new(m2p.outputs['Points'], sn.inputs['Geometry'])
    si = N.new('GeometryNodeSampleIndex'); si.data_type = 'FLOAT_VECTOR'
    L.new(m2p.outputs['Points'], si.inputs['Geometry'])
    L.new(pos_in.outputs['Position'], si.inputs['Value'])
    L.new(sn.outputs['Index'], si.inputs['Index'])
    sp = N.new('GeometryNodeSetPosition')
    L.new(c2p.outputs['Points'], sp.inputs['Geometry'])
    L.new(si.outputs[0], sp.inputs['Position'])

    rv_dens = N.new('FunctionNodeRandomValue')
    dens_lt = N.new('ShaderNodeMath'); dens_lt.operation = 'LESS_THAN'
    L.new(rv_dens.outputs[1], dens_lt.inputs[0]); dens_lt.inputs[1].default_value = density

    r2e = N.new('FunctionNodeRotationToEuler')
    L.new(c2p.outputs['Rotation'], r2e.inputs['Rotation'])
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(r2e.outputs['Euler'], sep.inputs['Vector'])

    sub_pi = N.new('ShaderNodeMath'); sub_pi.inputs[1].default_value = 1.5708
    L.new(sep.outputs['X'], sub_pi.inputs[0])
    mul_ps = N.new('ShaderNodeMath'); mul_ps.operation = 'MULTIPLY'
    L.new(sub_pi.outputs[0], mul_ps.inputs[0]); mul_ps.inputs[1].default_value = 0.2
    add_po = N.new('ShaderNodeMath')
    L.new(mul_ps.outputs[0], add_po.inputs[0]); add_po.inputs[1].default_value = pitch_offset
    comb_rot = N.new('ShaderNodeCombineXYZ')
    L.new(add_po.outputs[0], comb_rot.inputs['X']); L.new(sep.outputs['Z'], comb_rot.inputs['Z'])

    neg_pv = N.new('ShaderNodeMath'); neg_pv.operation = 'MULTIPLY'
    neg_pv.inputs[0].default_value = pitch_variance; neg_pv.inputs[1].default_value = -1.0
    rv_pitch = N.new('FunctionNodeRandomValue')
    L.new(neg_pv.outputs[0], rv_pitch.inputs[2]); rv_pitch.inputs[3].default_value = pitch_variance
    neg_yv = N.new('ShaderNodeMath'); neg_yv.operation = 'MULTIPLY'
    neg_yv.inputs[0].default_value = yaw_variance; neg_yv.inputs[1].default_value = -1.0
    rv_yaw = N.new('FunctionNodeRandomValue')
    L.new(neg_yv.outputs[0], rv_yaw.inputs[2]); rv_yaw.inputs[3].default_value = yaw_variance
    comb_var = N.new('ShaderNodeCombineXYZ')
    L.new(rv_pitch.outputs[1], comb_var.inputs['X']); L.new(rv_yaw.outputs[1], comb_var.inputs['Z'])

    add_rot = N.new('ShaderNodeVectorMath')
    L.new(comb_rot.outputs['Vector'], add_rot.inputs[0])
    L.new(comb_var.outputs['Vector'], add_rot.inputs[1])

    rv_scale = N.new('FunctionNodeRandomValue')
    rv_scale.inputs[2].default_value = min_scale; rv_scale.inputs[3].default_value = max_scale

    ci = N.new('GeometryNodeCollectionInfo')
    ci.inputs['Collection'].default_value = twig_col
    ci.inputs['Separate Children'].default_value = True
    ci.inputs['Reset Children'].default_value = True

    iop = N.new('GeometryNodeInstanceOnPoints')
    L.new(sp.outputs['Geometry'], iop.inputs['Points'])
    L.new(dens_lt.outputs[0], iop.inputs['Selection'])
    L.new(ci.outputs['Instances'], iop.inputs['Instance'])
    iop.inputs['Pick Instance'].default_value = True
    L.new(add_rot.outputs['Vector'], iop.inputs['Rotation'])
    L.new(rv_scale.outputs[1], iop.inputs['Scale'])

    ri = N.new('GeometryNodeRealizeInstances')
    L.new(iop.outputs['Instances'], ri.inputs['Geometry'])
    L.new(ri.outputs['Geometry'], go.inputs['Geometry'])

    mod = skel_obj.modifiers.new("DistTwigs", 'NODES'); mod.node_group = ng
    return mod


# ═══════════════════════════════════════════════════════════════════════════════
# Main bush builder
# ═══════════════════════════════════════════════════════════════════════════════

def make_bush():
    np.random.seed(SEED_VAL)
    att_scale = 0.2
    skel_scale = 0.35

    # ── 1. Build skeleton ──
    branch_config = {
        "n": 5,
        "spawn_kargs": lambda idx: {"rng": [0.5, 0.8]},
        "path_kargs": lambda idx: {"n_pts": 5, "sz": 0.4, "std": 1.4, "momentum": 0.4},
        "children": [],
    }
    tree_config = {
        "n": 1,
        "path_kargs": lambda idx: (
            {"n_pts": 3, "sz": 0.8, "std": 1, "momentum": 0.7} if idx > 0
            else {"n_pts": 3, "sz": 1, "std": 0.1, "momentum": 0.7}
        ),
        "spawn_kargs": lambda idx: {"init_vec": [0, 0, 1]},
        "children": [branch_config],
    }

    if SHRUB_SHAPE == 0:
        att_fn = lambda nodes: get_pts_sphere(2000, 7 * att_scale, [0, 0, 7 * att_scale])
    else:
        att_fn = lambda nodes: get_pts_cone_blender(2000, 5*att_scale, 5*att_scale, 10*att_scale, [0, 0, 9*att_scale])

    vtx = TreeVertices(np.array([[0.0, 0.0, 0.0]]))
    recursive_path(vtx, vtx.get_idxs(), level=0, **tree_config)
    space_colonization(vtx, atts=att_fn, D=0.3, s=0.4, d=10, n_steps=200,
                       level=max(vtx.level) + 1)

    # ── 2. Create skeleton mesh with attributes ──
    rev_depth = parse_tree_attributes(vtx)
    skel_obj = create_skeleton_mesh(vtx, rev_depth, skel_scale)

    # ── 3. Skin skeleton into tubes ──
    tube_obj = skeleton_to_mesh(skel_obj, min_radius=0.005, max_radius=0.025,
                                exponent=2.0, profile_res=20)

    # ── 3b. Apply bark material to main trunk tubes ──
    tube_obj.data.materials.clear()
    tube_obj.data.materials.append(BARK_MAT)

    # ── 4. Generate twig collection (with materials) ──
    twig_col = make_twig_collection(n_twigs=3, scale=att_scale, bark_mat=BARK_MAT)

    # ── 5. Instance twigs on skeleton ──
    mod = build_coll_distribute(skel_obj, twig_col,
                                depth_range=(0, 2.7), density=0.7, multi_inst=3,
                                min_scale=1.2 * att_scale, max_scale=1.4 * att_scale,
                                pitch_offset=1.0, pitch_variance=2.0, yaw_variance=2.0)
    bpy.ops.object.select_all(action="DESELECT")
    skel_obj.select_set(True); bpy.context.view_layer.objects.active = skel_obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # ── 6. Join tube mesh + instanced twigs ──
    bpy.ops.object.select_all(action="DESELECT")
    tube_obj.select_set(True); skel_obj.select_set(True)
    bpy.context.view_layer.objects.active = tube_obj
    bpy.ops.object.join()
    result = bpy.context.active_object

    # ── 7. Cleanup ──
    for o in list(twig_col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(twig_col)
    result.name = "BushFactory"
    bpy.ops.object.select_all(action="DESELECT")
    result.select_set(True); bpy.context.view_layer.objects.active = result
    bpy.ops.object.shade_smooth()
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Create materials and run
# ═══════════════════════════════════════════════════════════════════════════════

clear_scene()

# Pre-create all materials (seed-dependent)
BARK_MAT = create_bark_material(SEED)
BARK_MAT.use_fake_user = True
LEAF_MAT = create_leaf_material(SEED)
LEAF_MAT.use_fake_user = True
PETAL_MAT = create_petal_material(SEED)
PETAL_MAT.use_fake_user = True
CENTER_MAT = create_flower_center_material(SEED)
CENTER_MAT.use_fake_user = True

result = make_bush()
print(f"BushFactory: {len(result.data.vertices)} verts, "
      f"dims={tuple(round(d,3) for d in result.dimensions)}, "
      f"materials={[m.name for m in result.data.materials]}")
