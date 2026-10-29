# [FL_INDEX: keywords="blender_factory, procedural_3d, BoulderFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BoulderFactory | Category: factories_geo
# Prompt: A 3D model of a large boulder rendered from a slightly elevated three-quarter perspective. The boulder features a broad, flat-topped irregular shape with a highly rough and granular surface covered in fine pitting and erosion detail, a warm reddish-brown earth-toned coloring, and a wide low-profile silhouette resembling weathered sandstone or sedimentary rock.

import os
import math
import colorsys
from functools import reduce

import bmesh
import bpy
import numpy as np


SEED = int(os.environ.get("SEED", "0"))
# SEED-deterministic: seed_all(SEED) for material sampling; np.random.seed(seed) in build()


# ═══════════════════════════════════════════════════════════════════════════
#  Small RNG / color helpers
# ═══════════════════════════════════════════════════════════════════════════

def seed_all(seed):
    np.random.seed(seed)


def weighted_sample(registry):
    classes, weights = zip(*registry)
    weights = np.array(weights, dtype=float)
    idx = int(np.random.choice(len(classes), p=weights / weights.sum()))
    return classes[idx]


def clip01(x):
    return max(0.0, min(1.0, float(x)))


def _rgb_to_hsv_tuple(rgb):
    r, g, b = rgb[0], rgb[1], rgb[2]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return [h, s, v]


def _hsv_to_rgba_tuple(hsv, alpha=1.0):
    r, g, b = colorsys.hsv_to_rgb(hsv[0] % 1.0, clip01(hsv[1]), clip01(hsv[2]))
    return [r, g, b, alpha]


def clip_hsv(rgba, max_h=None, max_s=None, max_v=None):
    a = rgba[3] if len(rgba) == 4 else 1.0
    hsv = _rgb_to_hsv_tuple(rgba[:3])
    if max_h is not None:
        hsv[0] = hsv[0] * max_h
    if max_s is not None:
        hsv[1] = hsv[1] * max_s
    if max_v is not None:
        hsv[2] = hsv[2] * max_v
    return _hsv_to_rgba_tuple(hsv, a)


def random_color_neighbour(rgba, hue_diff=0.0, sat_diff=0.0, val_diff=0.0):
    a = rgba[3] if len(rgba) == 4 else 1.0
    hsv = _rgb_to_hsv_tuple(rgba[:3])

    def sample(x, diff):
        if diff is None:
            return float(np.random.uniform(0.0, 1.0))
        lb = max(0.0, x - diff)
        ub = min(1.0, x + diff)
        return float(np.random.uniform(lb, ub))

    hsv[0] = sample(hsv[0], hue_diff)
    hsv[1] = sample(hsv[1], sat_diff)
    hsv[2] = sample(hsv[2], val_diff)
    return _hsv_to_rgba_tuple(hsv, a)


# ═══════════════════════════════════════════════════════════════════════════
#  Inlined "mountain soil" palette (copied from
# ═══════════════════════════════════════════════════════════════════════════

MOUNTAIN_SOIL_PALETTE = {
    "hsv": [
        [0.07657200610458859, 0.6218981568424602, 0.568095301296071],
        [0.08871291011143334, 0.42452686112786103, 0.8104250687813854],
        [0.6140700215233733,  0.13288612784624504, 0.8730243901503021],
        [0.47346124527783656, 0.22768637564378527, 0.28529322850725286],
        [0.5961218425011782,  0.49810503051093324, 0.7223871831892953],
        [0.14544462943019612, 0.5389329914616029,  0.29703170640400595],
        [0.12202185913813124, 0.49872400694381797, 0.614810311196337],
        [0.02216908447486423, 0.027253574342521403,0.9994307999673898],
        [0.13984012270413265, 0.20105405545965413, 0.6344186455983115],
        [0.0620713740714641,  0.8670860688594698,  0.3201029563817151],
    ],
    "std": [
        [ 0.01789703571127652,0.0,0.0,-0.12597331599571596,0.1291790795498408,0.0,0.014011416277454765,0.016482971792371452,0.13343880210454545],
        [ 0.007744047862909046,0.0,0.0,0.012097193794030701,0.051526477352250744,0.0,0.003980522892370001,-0.019226818357123424,0.06316769321252796],
        [ 0.09980781923323018,0.0,0.0,-0.02751107358853669,0.07348168453829067,0.0,0.03823990807304074,0.007156125966110767,0.09896511745818332],
        [ 0.1554993390085664,0.0,0.0,0.06533844291739956,0.13682650189476622,0.0,0.009608147854344253,-0.058398154335554245,0.09181325340416716],
        [ 0.010030408116143077,0.0,0.0,0.036937285719487165,0.14591077523998403,0.0,-0.02501126600237874,-0.026409038081482275,0.10355895739448526],
        [ 0.06474239210522445,0.0,0.0,0.008133894434491999,0.20737552443259993,0.0,-0.007359426282875676,-0.05112646185112438,0.09877621827546076],
        [ 0.05182286396833515,0.0,0.0,0.051138327526411384,0.14230590221035327,0.0,0.0427792445588568,0.0022117825436210794,0.13239327935553516],
        [ 0.05822501097377041,0.0,0.0,0.07131802897006612,0.005299444518355579,0.0,-0.0012379613670810304,-5.4681679491867775e-05,0.0033877668057344145],
        [ 0.07661598914233601,0.0,0.0,-0.0018042105407654976,0.12477201699512865,0.0,-0.038383553414123014,-0.13518589408121312,0.21018245422010579],
        [ 0.03650937782912379,0.0,0.0,-0.024334393960077933,0.09154625092902843,0.0,0.0375423755906796,-0.0369424430932128,0.12079544868468167],
    ],
    "prob": [
        0.18173535415922157,
        0.12693188009479223,
        0.11203245756478104,
        0.10729577747369581,
        0.10508095198299697,
        0.08720755326805475,
        0.08547331599457036,
        0.06928970489547422,
        0.06438450615250647,
        0.060568498413906664,
    ],
}


def sample_mountain_soil_color():
    means = np.array(MOUNTAIN_SOIL_PALETTE["hsv"])
    stds = np.array(MOUNTAIN_SOIL_PALETTE["std"])
    probs = np.array(MOUNTAIN_SOIL_PALETTE["prob"])
    i = int(np.random.choice(np.arange(len(means)), 1, p=probs / probs.sum())[0])
    color = np.array(means[i]) + np.matmul(
        np.array(stds[i]).reshape((3, 3)),
        np.clip(np.random.randn(3), a_min=-1, a_max=1),
    )
    color[2] = max(min(color[2], 0.9), 0.1)
    rgb = np.array(colorsys.hsv_to_rgb(color[0], color[1], color[2]))
    rgb = np.clip(rgb, 0.0, 1.0)
    rgb = np.where(rgb >= 0.04045, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)
    return (float(rgb[0]), float(rgb[1]), float(rgb[2]), 1.0)


# ═══════════════════════════════════════════════════════════════════════════
#  shader_MOUNTAIN — faithful port of
#
#  Flags at call time for BoulderFactory: is_rock=True, snowy=False,
#  layered_mountain=True, num_layers=16, color=('palette','mountain soil'),
#  shader_roughness=1, prob_arranged_layers=0.1, random_seed=0.
# ═══════════════════════════════════════════════════════════════════════════

def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat


def make_mountain_material(name="BoulderMountain"):
    # Reseed to random_seed=0 exactly like FixedSeed(0) in shader_MOUNTAIN.
    np.random.seed(0)
    import random as _random
    _random.seed(0)

    # arranged_layers flag: uniform() > 0.1 means arranged_layers=True with prob 0.9
    arranged_layers = np.random.uniform() > 0.1
    shader_roughness = 1.0  # rg(1) == 1
    layered_mountain = True  # rg(True) == True
    num_layers = 16
    preset_zrange = (0, 120)
    hue_diff = 0.1
    max_sat = 0.4
    max_val = 0.4

    mat = _new_mat(name)
    nt = mat.node_tree
    ln = nt.links.new

    # tex_coor = Geometry node. Output 0 is Position, output 1 is Normal.
    tex_coor = nt.nodes.new("ShaderNodeNewGeometry")

    # z = separate xyz of Position, then map range
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ln(tex_coor.outputs[0], sep.inputs[0])

    z_map = nt.nodes.new("ShaderNodeMapRange")
    ln(sep.outputs[2], z_map.inputs[0])
    z_noise_mag = float(np.random.uniform(0.1, 0.4))
    z_min, z_max = preset_zrange
    z_map.inputs[1].default_value = float(z_min)
    z_map.inputs[2].default_value = float(z_max)
    z_map.inputs[3].default_value = -1.0 * (z_noise_mag / 2.0)
    z_map.inputs[4].default_value = 1.0 - (z_noise_mag / 2.0)

    # z_noise = NoiseTexture fed from Position, scale 0.1, detail 9
    z_noise_tex = nt.nodes.new("ShaderNodeTexNoise")
    ln(tex_coor.outputs[0], z_noise_tex.inputs["Vector"])
    z_noise_tex.inputs["Scale"].default_value = 0.1
    z_noise_tex.inputs["Detail"].default_value = 9.0

    z_noise_mul = nt.nodes.new("ShaderNodeMath")
    z_noise_mul.operation = "MULTIPLY"
    noise_out = z_noise_tex.outputs.get("Fac") or z_noise_tex.outputs[0]
    ln(noise_out, z_noise_mul.inputs[0])
    z_noise_mul.inputs[1].default_value = float(np.random.uniform(0.1, 0.3))

    z_add = nt.nodes.new("ShaderNodeMath")
    z_add.operation = "ADD"
    ln(z_map.outputs[0], z_add.inputs[0])
    ln(z_noise_mul.outputs[0], z_add.inputs[1])

    # Color ramp driven by z
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ln(z_add.outputs[0], ramp.inputs["Fac"])
    elements = ramp.color_ramp.elements
    # Remove one of the default elements (matches elements.remove(elements[0]))
    elements.remove(elements[0])
    # Exactly one element left (at position 1.0 by default)
    cur_color = sample_mountain_soil_color()  # 'palette','mountain soil'
    elements[-1].color = cur_color

    cur_loc = 1.0
    for _ in range(num_layers):
        if arranged_layers:
            cur_loc -= float(np.random.uniform()) * 2.0 / num_layers
            cur_loc = max(0.0, cur_loc)
        else:
            cur_loc = float(np.random.uniform())
        new_elem = elements.new(cur_loc)
        new_elem.color = sample_mountain_soil_color()

    # Ambient occlusion darkens color
    amb_occl = nt.nodes.new("ShaderNodeAmbientOcclusion")

    mix_ao = nt.nodes.new("ShaderNodeMixRGB")
    # positional input order: Fac=amb_occl, Color1=(0,0,0,1), Color2=ramp
    ao_out = amb_occl.outputs.get("AO") or amb_occl.outputs[0]
    ln(ao_out, mix_ao.inputs["Fac"])
    mix_ao.inputs["Color1"].default_value = (0.0, 0.0, 0.0, 1.0)
    ln(ramp.outputs["Color"], mix_ao.inputs["Color2"])

    # color_ = ramp * max(0.2, |dot((0,0,1), normal)|^3)
    geom_for_normal = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[0].default_value = (0.0, 0.0, 1.0)
    ln(geom_for_normal.outputs["Normal"], dot.inputs[1])

    abs_dot = nt.nodes.new("ShaderNodeVectorMath")
    abs_dot.operation = "ABSOLUTE"
    ln(dot.outputs.get("Value") or dot.outputs[0], abs_dot.inputs[0])

    pow_dot = nt.nodes.new("ShaderNodeMath")
    pow_dot.operation = "POWER"
    ln(abs_dot.outputs.get("Value") or abs_dot.outputs[0], pow_dot.inputs[0])
    pow_dot.inputs[1].default_value = 3.0

    max_shade = nt.nodes.new("ShaderNodeMath")
    max_shade.operation = "MAXIMUM"
    max_shade.inputs[0].default_value = 0.2
    ln(pow_dot.outputs[0], max_shade.inputs[1])

    # multiply ramp (post-AO) by shading scalar
    color_out = nt.nodes.new("ShaderNodeVectorMath")
    color_out.operation = "MULTIPLY"
    ln(mix_ao.outputs["Color"], color_out.inputs[0])
    ln(max_shade.outputs[0], color_out.inputs[1])

    # snowy=False → no snow overlay
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(color_out.outputs["Vector"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = float(shader_roughness)

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# ═══════════════════════════════════════════════════════════════════════════
#  shader_stone — faithful port of
#
#  We only need the color / roughness half (geometry=False branch).
#  Musgrave → NoiseTexture fallback (Blender 5.0 removed Musgrave).
# ═══════════════════════════════════════════════════════════════════════════

def sample_ratio(x, sample_min=0.5, sample_max=2):
    if x == 0:
        return x
    neg = 1
    if x < 0:
        x = -x
        neg = -1
    x_min = x * sample_min
    x_max = x * sample_max
    import random as _random
    y = _random.random() * (math.log(x_max) - math.log(x_min)) + math.log(x_min)
    return neg * math.exp(y)


def sample_color_channels_rgba(color_elem, offset=0):
    """Port of sample_color(..., keep_sum=False) for a ColorRamp element."""

    import random as _random
    new = [color_elem[0], color_elem[1], color_elem[2], color_elem[3]]
    for i in range(3):
        if offset == 0:
            new[i] = _random.random()
        else:
            new[i] += (_random.random() - 0.5) * 2 * offset
        new[i] = clip01(new[i])
    color_elem[0], color_elem[1], color_elem[2], color_elem[3] = new[0], new[1], new[2], new[3]


def make_stone_material(name="BoulderStone"):
    # FixedSeed inside shader_stone resets np.random AND python random to 0.
    np.random.seed(0)
    import random as _random
    _random.seed(0)

    size_bumps_lf = float(np.random.uniform(0, 30))
    heig_bumps_lf_val = float(np.random.uniform(0.08, 0.15))
    dens_crack = float(np.random.uniform(0, 0.1))
    scal_crack = float(np.random.uniform(5, 10) / 2)
    widt_crack = float(np.random.uniform(0.08, 0.12))
    scale = 0.5

    # pre-sample all nw.new_value(uniform()) parameters in order
    musgrave_w = float(np.random.uniform(0, 10))
    noise_w = float(np.random.uniform(0, 10))
    noise_2_w = float(np.random.uniform(0, 10))
    noise_1_w = float(np.random.uniform(0, 10))
    wave_scale = float(np.random.normal(2, 0.5))
    wave_distortion = float(np.random.normal(6, 2))
    wave_detail = float(np.random.normal(15, 5))
    noise_3_w = float(np.random.uniform(0, 10))
    noise_3_scale = sample_ratio(5, 3 / 4, 4 / 3)
    noise_4_scale = sample_ratio(20, 3 / 4, 4 / 3)
    noise_4_w = float(np.random.uniform(0, 10))

    # Stone color-ramp base colors
    color1 = float(np.random.uniform(0, 0.05))
    color2 = float(np.random.uniform(0.05, 0.1))
    color3 = float(np.random.uniform(0, 0.05))
    rough_min = float(np.random.uniform(0.6, 0.7))
    rough_max = float(np.random.uniform(0.7, 0.8))

    mat = _new_mat(name)
    nt = mat.node_tree
    ln = nt.links.new

    # In shader graphs, position = NewGeometry, normal = NewGeometry's Normal out
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    # shader_stone treats `position` as the whole geometry node (used as vector input,
    # which defaults to reading Position output).
    position_out = geom.outputs["Position"]
    normal_out = geom.outputs["Normal"]

    # --- Low-frequency bumps (Musgrave replacement = NoiseTexture) ---
    bumps_noise = nt.nodes.new("ShaderNodeTexNoise")
    bumps_noise.noise_dimensions = "4D"
    ln(position_out, bumps_noise.inputs["Vector"])
    bumps_noise.inputs["Scale"].default_value = size_bumps_lf * scale
    if "W" in bumps_noise.inputs:
        bumps_noise.inputs["W"].default_value = musgrave_w
    bumps_fac = bumps_noise.outputs.get("Fac") or bumps_noise.outputs[0]

    v1 = nt.nodes.new("ShaderNodeVectorMath")
    v1.operation = "MULTIPLY"
    ln(bumps_fac, v1.inputs[0])
    ln(normal_out, v1.inputs[1])

    v3 = nt.nodes.new("ShaderNodeVectorMath")
    v3.operation = "MULTIPLY"
    ln(v1.outputs["Vector"], v3.inputs[0])
    v3.inputs[1].default_value = (heig_bumps_lf_val,) * 3

    # --- Mid-frequency detail noise ---
    noise_texture = nt.nodes.new("ShaderNodeTexNoise")
    noise_texture.noise_dimensions = "4D"
    ln(position_out, noise_texture.inputs["Vector"])
    noise_texture.inputs["Scale"].default_value = 12.0 * scale
    noise_texture.inputs["Detail"].default_value = 16.0
    if "W" in noise_texture.inputs:
        noise_texture.inputs["W"].default_value = noise_w
    n_fac = noise_texture.outputs.get("Fac") or noise_texture.outputs[0]

    v_noise_norm = nt.nodes.new("ShaderNodeVectorMath")
    v_noise_norm.operation = "MULTIPLY"
    ln(n_fac, v_noise_norm.inputs[0])
    ln(normal_out, v_noise_norm.inputs[1])

    v_noise_scaled = nt.nodes.new("ShaderNodeVectorMath")
    v_noise_scaled.operation = "MULTIPLY"
    ln(v_noise_norm.outputs["Vector"], v_noise_scaled.inputs[0])
    v_noise_scaled.inputs[1].default_value = (0.1,) * 3

    v6 = nt.nodes.new("ShaderNodeVectorMath")
    v6.operation = "ADD"
    ln(v3.outputs["Vector"], v6.inputs[0])
    ln(v_noise_scaled.outputs["Vector"], v6.inputs[1])

    # --- Crack density mask ---
    noise_tex_2 = nt.nodes.new("ShaderNodeTexNoise")
    noise_tex_2.noise_dimensions = "4D"
    ln(position_out, noise_tex_2.inputs["Vector"])
    noise_tex_2.inputs["Scale"].default_value = 5.0 * scale
    if "W" in noise_tex_2.inputs:
        noise_tex_2.inputs["W"].default_value = noise_2_w
    n2_fac = noise_tex_2.outputs.get("Fac") or noise_tex_2.outputs[0]

    ramp2 = nt.nodes.new("ShaderNodeValToRGB")
    ln(n2_fac, ramp2.inputs["Fac"])
    ramp2.color_ramp.elements[0].position = 0.445 + (2 * dens_crack) - 0.1
    ramp2.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    ramp2.color_ramp.elements[1].position = 0.505 + (2 * dens_crack) - 0.1
    ramp2.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # --- Crack wave mask ---
    noise_tex_1 = nt.nodes.new("ShaderNodeTexNoise")
    noise_tex_1.noise_dimensions = "4D"
    ln(position_out, noise_tex_1.inputs["Vector"])
    noise_tex_1.inputs["Scale"].default_value = 1.0 * scale
    noise_tex_1.inputs["Detail"].default_value = 16.0
    if "W" in noise_tex_1.inputs:
        noise_tex_1.inputs["W"].default_value = noise_1_w

    wave = nt.nodes.new("ShaderNodeTexWave")
    ln(noise_tex_1.outputs["Color"], wave.inputs["Vector"])
    wave.inputs["Scale"].default_value = wave_scale
    wave.inputs["Distortion"].default_value = wave_distortion
    wave.inputs["Detail"].default_value = wave_detail
    wave_fac = wave.outputs.get("Fac") or wave.outputs[0]

    ramp1 = nt.nodes.new("ShaderNodeValToRGB")
    ln(wave_fac, ramp1.inputs["Fac"])
    ramp1.color_ramp.elements[0].position = 0.0
    ramp1.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    ramp1.color_ramp.elements[1].position = widt_crack
    ramp1.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # mix = MixRGB(Fac=ramp2, Color1=ramp1, Color2=default)
    mix = nt.nodes.new("ShaderNodeMixRGB")
    ln(ramp2.outputs["Color"], mix.inputs["Fac"])
    ln(ramp1.outputs["Color"], mix.inputs["Color1"])

    # --- Fine detail 1 ---
    noise_tex_3 = nt.nodes.new("ShaderNodeTexNoise")
    noise_tex_3.noise_dimensions = "4D"
    ln(position_out, noise_tex_3.inputs["Vector"])
    noise_tex_3.inputs["Scale"].default_value = noise_3_scale
    if "W" in noise_tex_3.inputs:
        noise_tex_3.inputs["W"].default_value = noise_3_w
    n3_fac = noise_tex_3.outputs.get("Fac") or noise_tex_3.outputs[0]

    # --- Fine detail 2 ---
    noise_tex_4 = nt.nodes.new("ShaderNodeTexNoise")
    noise_tex_4.noise_dimensions = "4D"
    ln(position_out, noise_tex_4.inputs["Vector"])
    noise_tex_4.inputs["Scale"].default_value = noise_4_scale
    if "W" in noise_tex_4.inputs:
        noise_tex_4.inputs["W"].default_value = noise_4_w
    n4_fac = noise_tex_4.outputs.get("Fac") or noise_tex_4.outputs[0]

    ramp5 = nt.nodes.new("ShaderNodeValToRGB")
    ln(n4_fac, ramp5.inputs["Fac"])
    # Original uses 4 elements
    while len(ramp5.color_ramp.elements) < 4:
        ramp5.color_ramp.elements.new(0.0)
    ramp5.color_ramp.elements[0].position = 0.0
    ramp5.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    ramp5.color_ramp.elements[1].position = 0.3
    ramp5.color_ramp.elements[1].color = (0.5, 0.5, 0.5, 1.0)
    ramp5.color_ramp.elements[2].position = 0.7
    ramp5.color_ramp.elements[2].color = (0.5, 0.5, 0.5, 1.0)
    ramp5.color_ramp.elements[3].position = 1.0
    ramp5.color_ramp.elements[3].color = (1.0, 1.0, 1.0, 1.0)

    # --- Base color ramp (driven by noise_texture) ---
    colorramp = nt.nodes.new("ShaderNodeValToRGB")
    ln(n_fac, colorramp.inputs["Fac"])
    while len(colorramp.color_ramp.elements) < 3:
        colorramp.color_ramp.elements.new(1.0)
    colorramp.color_ramp.elements[0].position = 0.223
    colorramp.color_ramp.elements[0].color = (color1, color1, color1, 1.0)
    colorramp.color_ramp.elements[1].position = 0.509
    colorramp.color_ramp.elements[1].color = (color2, color2, color2, 1.0)
    colorramp.color_ramp.elements[2].position = 1.0
    colorramp.color_ramp.elements[2].color = (color3, color3, color3, 1.0)
    sample_color_channels_rgba(colorramp.color_ramp.elements[1].color, offset=0.01)
    sample_color_channels_rgba(colorramp.color_ramp.elements[2].color, offset=0.01)

    # stone_base_color = MixRGB(Fac=mix, Color1=(0,0,0,1), Color2=colorramp)
    stone_base = nt.nodes.new("ShaderNodeMixRGB")
    ln(mix.outputs["Color"], stone_base.inputs["Fac"])
    stone_base.inputs["Color1"].default_value = (0.0, 0.0, 0.0, 1.0)
    ln(colorramp.outputs["Color"], stone_base.inputs["Color2"])

    # stone_roughness color ramp
    ramp3 = nt.nodes.new("ShaderNodeValToRGB")
    ln(n_fac, ramp3.inputs["Fac"])
    ramp3.color_ramp.elements[0].position = 0.082
    ramp3.color_ramp.elements[0].color = (rough_min, rough_min, rough_min, 1.0)
    ramp3.color_ramp.elements[1].position = 0.768
    ramp3.color_ramp.elements[1].color = (rough_max, rough_max, rough_max, 1.0)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(stone_base.outputs["Color"], bsdf.inputs["Base Color"])
    ln(ramp3.outputs["Color"], bsdf.inputs["Roughness"])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# ═══════════════════════════════════════════════════════════════════════════
#  Material registry — matches material_assignments.rock
# ═══════════════════════════════════════════════════════════════════════════

ROCK_REGISTRY = [
    (make_mountain_material, 5),
    (make_stone_material, 1),
]


def get_rock_material(name="BoulderRockMaterial"):
    # random_general.weighted_sample applied to the `rock` registry.
    builder = weighted_sample(ROCK_REGISTRY)
    return builder(name=name)


# ═══════════════════════════════════════════════════════════════════════════
#  __init__ FixedSeed(factory_seed) call order).
#    1) rock_surface class via weighted_sample(rock)
#    2) method via np.random.choice(configs, p=weights)   ← consumed here,
#       but the geometry function below ALSO calls np.random.choice with
#       another fresh np.random.seed(seed) in build(), so we don't rely on
#       this single draw for is_slab in the geometry.
# ═══════════════════════════════════════════════════════════════════════════

seed_all(SEED)
CATEG_MAT = get_rock_material(name="BoulderFactory_Material")
CATEG_MAT.use_fake_user = True
# Replicate the __init__ np.random.choice call so the RNG state exactly
_ = np.random.choice(["boulder", "slab"], p=[0.8, 0.2])


# ═══════════════════════════════════════════════════════════════════════════
#  GEOMETRY (copied verbatim from objects_blender/rocks/BoulderFactory.py)
# ═══════════════════════════════════════════════════════════════════════════

def log_uniform(a, b, size=None):
    return np.exp(np.random.uniform(np.log(a), np.log(b), size=size))

# ---- Blender helpers ----

def _select_none():
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    if bpy.context.active_object:
        bpy.context.active_object.select_set(False)

class SelectObjects:
    def __init__(self, objs, active=0):
        self.objs = objs if isinstance(objs, (list, tuple)) else [objs]
        self.active = active
    def __enter__(self):
        self.prev_sel = list(bpy.context.selected_objects)
        self.prev_active = bpy.context.view_layer.objects.active
        _select_none()
        for o in self.objs:
            if o and o.name in bpy.data.objects:
                o.select_set(True)
        if self.objs:
            bpy.context.view_layer.objects.active = self.objs[self.active]
            self.objs[self.active].select_set(True)
        return self
    def __exit__(self, *_):
        _select_none()
        for o in self.prev_sel or []:
            if o and o.name in bpy.data.objects:
                o.select_set(True)
        if self.prev_active and self.prev_active.name in bpy.data.objects:
            bpy.context.view_layer.objects.active = self.prev_active

def apply_transform(obj, loc=False, rot=True, scale=True):
    with SelectObjects(obj):
        bpy.ops.object.transform_apply(location=loc, rotation=rot, scale=scale)
    return obj

def modify_mesh(obj, type, apply=True, **kwargs):
    mod = obj.modifiers.new(name=type, type=type)
    mod.show_viewport = not apply
    for k, v in kwargs.items():
        try:
            setattr(mod, k, v)
        except Exception:
            pass
    if apply:
        with SelectObjects(obj):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception:
                pass
    return obj

# ---- Convex hull mesh ----

def convex_hull_obj(vertices):
    """Create a mesh object from convex hull of given vertices."""

    try:
        import trimesh
        import trimesh.convex
        hull = trimesh.convex.convex_hull(vertices)
        mesh = bpy.data.meshes.new('boulder_hull')
        mesh.from_pydata(np.asarray(hull.vertices).tolist(),
                         [], np.asarray(hull.faces).tolist())
        mesh.update()
    except Exception:
        pts = np.asarray(vertices)
        mesh = bpy.data.meshes.new('boulder_hull')
        mesh.from_pydata(pts.tolist(), [], [])
        bm = bmesh.new()
        bm.from_mesh(mesh)
        try:
            bmesh.ops.convex_hull(bm, input=bm.verts, use_existing_faces=False)
        except Exception:
            pass
        bm.to_mesh(mesh)
        bm.free()
    obj = bpy.data.objects.new('boulder_hull', mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj

# ---- GeoNodes helpers ----

def _ng_inputs(node_group):
    return {s.name: s for s in node_group.interface.items_tree if s.in_out == 'INPUT'}

def _infer_output_socket(item):
    if isinstance(item, bpy.types.NodeSocket):
        return item
    if isinstance(item, tuple) and len(item) == 2 and hasattr(item[0], 'outputs'):
        node, sock = item
        return node.outputs[sock]
    if hasattr(item, 'outputs') and len(getattr(item, 'outputs', [])):
        for s in item.outputs:
            if getattr(s, 'enabled', True):
                return s
        return item.outputs[0]
    return None

class NodeWrangler:
    def __init__(self, node_group):
        self.node_group = node_group
        self.nodes = node_group.nodes
        self.links = node_group.links

    def _group_io(self, bl_idname):
        for n in self.nodes:
            if n.bl_idname == bl_idname:
                return n
        return self.nodes.new(bl_idname)

    def connect_input(self, sock, item):
        out = _infer_output_socket(item)
        if out is not None:
            self.links.new(out, sock)
        else:
            try:
                sock.default_value = item
            except Exception:
                try:
                    sock.default_value = tuple(item)
                except Exception:
                    pass

    def new_node(self, node_type, input_args=None, attrs=None,
                 input_kwargs=None, expose_input=None):
        if expose_input:
            for spec in expose_input:
                if len(spec) == 3:
                    dtype, name, val = spec
                else:
                    dtype, name, val = None, spec[0], (spec[1] if len(spec) > 1 else None)
                self.expose_input(name, val=val, dtype=dtype)
        n = self.nodes.new(node_type)
        if attrs:
            for k, v in attrs.items():
                try:
                    setattr(n, k, v)
                except Exception:
                    pass
        if input_args:
            for i, item in enumerate(input_args):
                if item is not None and i < len(n.inputs):
                    self.connect_input(n.inputs[i], item)
        if input_kwargs:
            for k, item in input_kwargs.items():
                try:
                    self.connect_input(n.inputs[k], item)
                except Exception:
                    try:
                        idx = [s.name for s in n.inputs].index(k)
                        self.connect_input(n.inputs[idx], item)
                    except Exception:
                        pass
        return n

    def expose_input(self, name, val=None, dtype=None):
        gi = self._group_io('NodeGroupInput')
        if name not in _ng_inputs(self.node_group):
            if dtype and isinstance(dtype, str) and dtype.startswith('NodeSocket'):
                sock_type = dtype
            elif isinstance(val, bool):
                sock_type = 'NodeSocketBool'
            elif isinstance(val, int):
                sock_type = 'NodeSocketInt'
            elif isinstance(val, float):
                sock_type = 'NodeSocketFloat'
            elif isinstance(val, (tuple, list)) and len(val) == 3:
                sock_type = 'NodeSocketVector'
            else:
                sock_type = 'NodeSocketFloat'
            self.node_group.interface.new_socket(name=name, in_out='INPUT',
                                                  socket_type=sock_type)
        try:
            return gi.outputs[name]
        except Exception:
            idx = list(_ng_inputs(self.node_group).keys()).index(name)
            return gi.outputs[idx]

    def compare(self, op, a, b):
        return self.new_node('FunctionNodeCompare',
                             input_kwargs={'A': a, 'B': b},
                             attrs={'data_type': 'FLOAT', 'operation': op})

    def boolean_math(self, op, *xs):
        vals = list(xs)
        if all(isinstance(v, bool) for v in vals):
            if op == 'AND': return all(vals)
            if op == 'OR': return any(vals)
        cur = vals[0]
        for v in vals[1:]:
            cur = self.new_node('FunctionNodeBooleanMath',
                                input_kwargs={'Boolean': cur, 'Boolean_001': v},
                                attrs={'operation': op})
        return cur

    def bernoulli(self, p):
        return bool(np.random.rand() < float(p))

    def uniform(self, a, b):
        return float(np.random.uniform(float(a), float(b)))

    def compare_direction(self, op, vec_a, vec_b, angle):
        na = self.new_node('ShaderNodeVectorMath',
                           input_kwargs={'Vector': vec_a},
                           attrs={'operation': 'NORMALIZE'})
        nb = self.new_node('ShaderNodeVectorMath',
                           input_kwargs={'Vector': vec_b},
                           attrs={'operation': 'NORMALIZE'})
        dot = self.new_node('ShaderNodeVectorMath',
                            input_kwargs={'Vector': (na, 'Vector'),
                                          'Vector_001': (nb, 'Vector')},
                            attrs={'operation': 'DOT_PRODUCT'})
        thresh = float(math.cos(float(angle)))
        cmp_op = 'GREATER_THAN' if op == 'LESS_THAN' else 'LESS_THAN'
        return self.new_node('FunctionNodeCompare',
                             input_kwargs={'A': (dot, 'Value'), 'B': thresh},
                             attrs={'data_type': 'FLOAT', 'operation': cmp_op})

# ---- GeoNodes modifier helper ----

def add_geomod(obj, geo_func, apply=False):
    ng = bpy.data.node_groups.new('GeoMod', 'GeometryNodeTree')
    if 'Geometry' not in _ng_inputs(ng):
        ng.interface.new_socket(name='Geometry', in_out='INPUT',
                                socket_type='NodeSocketGeometry')
    ng_outs = {s.name: s for s in ng.interface.items_tree if s.in_out == 'OUTPUT'}
    if 'Geometry' not in ng_outs:
        ng.interface.new_socket(name='Geometry', in_out='OUTPUT',
                                socket_type='NodeSocketGeometry')
    mod = obj.modifiers.new('GeoMod', 'NODES')
    mod.node_group = ng
    nw = NodeWrangler(ng)
    geo_func(nw)
    if apply:
        with SelectObjects(obj):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception:
                pass
    return mod

# ---- Node type constants ----

class Nodes:
    AttributeStatistic = 'GeometryNodeAttributeStatistic'
    ExtrudeMesh = 'GeometryNodeExtrudeMesh'
    GroupInput = 'NodeGroupInput'
    GroupOutput = 'NodeGroupOutput'
    InputMeshFaceArea = 'GeometryNodeInputMeshFaceArea'
    InputNormal = 'GeometryNodeInputNormal'
    InputPosition = 'GeometryNodeInputPosition'
    ScaleElements = 'GeometryNodeScaleElements'
    SetPosition = 'GeometryNodeSetPosition'
    StoreNamedAttribute = 'GeometryNodeStoreNamedAttribute'

# ---- geo_extrusion ----

def geo_extrusion(nw, extrude_scale=1):
    from numpy.random import uniform
    geometry = nw.new_node(Nodes.GroupInput,
                           expose_input=[('NodeSocketGeometry', 'Geometry', None)])
    face_area = nw.new_node(Nodes.InputMeshFaceArea)

    tops = []
    extrude_configs = [(uniform(0.2, 0.3), 0.8, 0.4), (0.6, 0.2, 0.6)]
    top_facing = nw.compare_direction(
        'LESS_THAN', nw.new_node(Nodes.InputNormal), (0, 0, 1), np.pi * 2 / 3
    )
    for prob, extrude, scale in extrude_configs:
        extrude = extrude * extrude_scale
        face_area_stats = nw.new_node(
            Nodes.AttributeStatistic,
            [geometry, None, face_area],
            attrs={'domain': 'FACE'},
        ).outputs
        selection = reduce(
            lambda *xs: nw.boolean_math('AND', *xs),
            [
                top_facing,
                nw.bernoulli(prob),
                nw.compare('GREATER_THAN', face_area, face_area_stats['Mean']),
            ],
        )
        geometry, top, side = nw.new_node(
            Nodes.ExtrudeMesh,
            [geometry, selection, None, nw.uniform(extrude * 0.5, extrude)],
        ).outputs
        geometry = nw.new_node(
            Nodes.ScaleElements, [geometry, top, nw.uniform(scale * 0.5, scale)]
        )
        tops.append(top)

    geometry = nw.new_node(
        Nodes.StoreNamedAttribute,
        input_kwargs={
            'Geometry': geometry,
            'Name': 'top',
            'Value': reduce(lambda *xs: nw.boolean_math('OR', *xs), tops),
        },
    )
    nw.new_node(Nodes.GroupOutput, input_kwargs={'Geometry': geometry})

# ---- geo_extension: Musgrave-equivalent radial noise displacement ----

def geo_extension(nw, noise_strength=0.2, noise_scale=2.0):
    ns = float(np.random.uniform(noise_strength / 2, noise_strength))
    sc = float(np.random.uniform(noise_scale * 0.7, noise_scale * 1.4))
    random_offset = tuple(np.random.uniform(-1, 1, 3).tolist())

    geometry = nw.new_node(Nodes.GroupInput,
                           expose_input=[('NodeSocketGeometry', 'Geometry', None)])
    pos = nw.new_node(Nodes.InputPosition)

    length = nw.new_node('ShaderNodeVectorMath',
                          input_kwargs={'Vector': pos},
                          attrs={'operation': 'LENGTH'})
    inv_length = nw.new_node('ShaderNodeMath',
                              attrs={'operation': 'DIVIDE'},
                              input_args=[1.0, (length, 'Value')])
    direction = nw.new_node('ShaderNodeVectorMath',
                             attrs={'operation': 'SCALE'},
                             input_kwargs={'Vector': pos, 'Scale': inv_length})

    direction = nw.new_node('ShaderNodeVectorMath',
                             attrs={'operation': 'ADD'},
                             input_kwargs={'Vector': (direction, 'Vector'),
                                           'Vector_001': random_offset})

    noise = nw.new_node('ShaderNodeTexNoise',
                         input_kwargs={
                             'Vector': (direction, 'Vector'),
                             'Scale': sc,
                             'Detail': 1.0,
                             'Roughness': 0.25,
                             'Lacunarity': 2.0,
                         },
                         attrs={'noise_dimensions': '3D', 'normalize': False})

    noise_biased = nw.new_node('ShaderNodeMath', attrs={'operation': 'ADD'},
                                input_args=[noise, 0.25])
    musgrave = nw.new_node('ShaderNodeMath', attrs={'operation': 'MULTIPLY'},
                            input_args=[noise_biased, ns])

    offset = nw.new_node('ShaderNodeVectorMath', attrs={'operation': 'SCALE'},
                          input_kwargs={'Vector': pos, 'Scale': musgrave})
    geometry = nw.new_node(Nodes.SetPosition,
                           input_kwargs={'Geometry': geometry, 'Offset': offset})
    nw.new_node(Nodes.GroupOutput, input_kwargs={'Geometry': geometry})

# ---- Build ----

def build(seed=0):
    from numpy.random import uniform
    np.random.seed(seed)

    is_slab = np.random.choice([False, True], p=[0.8, 0.2])

    _select_none()

    # 1. Convex hull from random points
    vertices = np.random.uniform(-1, 1, (32, 3))
    obj = convex_hull_obj(vertices)

    # 2. Geo extrusion
    add_geomod(obj, geo_extrusion, apply=True)

    # 3. Subdivision
    modify_mesh(obj, 'SUBSURF', render_levels=2, levels=2,
                subdivision_type='SIMPLE')

    # 4. Offset upward and scale
    obj.location[2] += obj.dimensions[2] * 0.2
    apply_transform(obj, loc=True)
    if is_slab:
        obj.scale = *log_uniform(0.5, 2.0, 2), log_uniform(0.1, 0.15)
    else:
        obj.scale = *log_uniform(0.4, 1.2, 2), log_uniform(0.4, 0.8)
    apply_transform(obj)

    # 5. Slight rotation
    obj.rotation_euler[0] = uniform(-np.pi / 24, np.pi / 24)
    apply_transform(obj)
    obj.rotation_euler[2] = uniform(0, np.pi * 2)
    apply_transform(obj)

    # 6. Convert stored "top" attribute to vertex group for BEVEL
    with SelectObjects(obj):
        try:
            bpy.ops.geometry.attribute_convert(mode='VERTEX_GROUP')
        except Exception:
            pass

    # 7. Bevel non-top faces
    if obj.vertex_groups.get('top'):
        modify_mesh(obj, 'BEVEL', limit_method='VGROUP', vertex_group='top',
                    invert_vertex_group=True, offset_type='PERCENT', width_pct=10)

    # 8. Sharp remesh
    modify_mesh(obj, 'REMESH', mode='SHARP', octree_depth=3)

    # 9. Noise displacement (geo_extension)
    add_geomod(obj, geo_extension, apply=True)

    # 10. Voronoi displacement
    for ns in [log_uniform(0.2, 0.5), log_uniform(0.05, 0.1)]:
        voronoi_tex = bpy.data.textures.new('boulder_voronoi', 'VORONOI')
        voronoi_tex.noise_scale = float(ns)
        voronoi_tex.distance_metric = 'DISTANCE'
        modify_mesh(obj, 'DISPLACE', texture=voronoi_tex,
                    strength=0.01, mid_level=0)

    # 11. Voxel remesh
    modify_mesh(obj, 'REMESH', mode='VOXEL', voxel_size=0.005625)

    obj.name = 'BoulderFactory'
    return obj

# ---- Main ----

bpy.context.scene.cursor.location = (0, 0, 0)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

result = build(SEED)
result.data.materials.clear()
result.data.materials.append(CATEG_MAT)

print(f"BoulderFactory built: {len(result.data.vertices)} verts, "
      f"{len(result.data.polygons)} faces, "
      f"material slots={len(result.data.materials)}")
