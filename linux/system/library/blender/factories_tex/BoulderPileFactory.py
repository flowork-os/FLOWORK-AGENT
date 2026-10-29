# [FL_INDEX: keywords="blender_factory, procedural_3d, BoulderPileFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BoulderPileFactory | Category: factories_tex
# Prompt: A 3D model of a pile of boulders rendered from a slightly elevated three-quarter perspective. The pile features a cluster of approximately eight to twelve individual rough-surfaced rocks of varying sizes stacked and scattered together in a natural heap arrangement, with gray stone coloring and irregular angular shapes casting shadows on the ground plane.

"""
BoulderPileFactory -- textured variant.

Geometry: copied verbatim from ``objects_blender/rocks/BoulderPileFactory.py``.
Shader:   faithful in-line replica of ``rock`` registry, which in

              rock = [
                  (terrain.Mountain, 5),
                  (terrain.Stone,    1),
              ]

          BoulderFactory.__init__ samples it with ``FixedSeed(factory_seed)``
          and applies the chosen surface to every boulder in the pile; this
          script mirrors that using the raw ``SEED`` environment variable.

No wear_tear is applied: neither BoulderFactory nor BoulderPileFactory in
drive scratches / edge_wear on rock objects.
"""


import os
import json
import math
import colorsys
import random
from functools import reduce

import bpy
import bmesh
import numpy as np
from numpy.random import uniform

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1 SETUP -- material sampling on raw SEED
# ─────────────────────────────────────────────────────────────────────────────

SEED = int(os.environ.get("SEED", "0"))

def _seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)

# ═════════════════════════════════════════════════════════════════════════════
# ═════════════════════════════════════════════════════════════════════════════
#
# Sources:
#
# Both shaders wrap their randomized color-ramp construction in
# ``FixedSeed(random_seed=0)``, so the shader appearance is deterministic per
# surface class.  The only variation between seeds comes from which surface
# class the registry sampler picks (Mountain with weight 5, Stone with 1).

def _new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _principled_color_inputs(bsdf):
    """Return the principled-BSDF 'specular' socket name that exists in this build."""

    return "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"

def _fac_output(node):
    return node.outputs.get("Fac") or node.outputs.get("Factor") or node.outputs[0]

_PALETTE_MOUNTAIN_SOIL = {
    "hsv": [
        [0.07657200610458859, 0.6218981568424602, 0.568095301296071],
        [0.08871291011143334, 0.42452686112786103, 0.8104250687813854],
        [0.6140700215233733, 0.13288612784624504, 0.8730243901503021],
        [0.47346124527783656, 0.22768637564378527, 0.28529322850725286],
        [0.5961218425011782, 0.49810503051093324, 0.7223871831892953],
        [0.14544462943019612, 0.5389329914616029, 0.29703170640400595],
        [0.12202185913813124, 0.49872400694381797, 0.614810311196337],
        [0.02216908447486423, 0.027253574342521403, 0.9994307999673898],
        [0.13984012270413265, 0.20105405545965413, 0.6344186455983115],
        [0.0620713740714641, 0.8670860688594698, 0.3201029563817151],
    ],
    "std": [
        [0.01789703571127652, 0.0, 0.0, -0.12597331599571596, 0.1291790795498408, 0.0, 0.014011416277454765, 0.016482971792371452, 0.13343880210454545],
        [0.007744047862909046, 0.0, 0.0, 0.012097193794030701, 0.051526477352250744, 0.0, 0.003980522892370001, -0.019226818357123424, 0.06316769321252796],
        [0.09980781923323018, 0.0, 0.0, -0.02751107358853669, 0.07348168453829067, 0.0, 0.03823990807304074, 0.007156125966110767, 0.09896511745818332],
        [0.1554993390085664, 0.0, 0.0, 0.06533844291739956, 0.13682650189476622, 0.0, 0.009608147854344253, -0.058398154335554245, 0.09181325340416716],
        [0.010030408116143077, 0.0, 0.0, 0.036937285719487165, 0.14591077523998403, 0.0, -0.02501126600237874, -0.026409038081482275, 0.10355895739448526],
        [0.06474239210522445, 0.0, 0.0, 0.008133894434491999, 0.20737552443259993, 0.0, -0.007359426282875676, -0.05112646185112438, 0.09877621827546076],
        [0.05182286396833515, 0.0, 0.0, 0.051138327526411384, 0.14230590221035327, 0.0, 0.0427792445588568, 0.0022117825436210794, 0.13239327935553516],
        [0.05822501097377041, 0.0, 0.0, 0.07131802897006612, 0.005299444518355579, 0.0, -0.0012379613670810304, -5.4681679491867775e-05, 0.0033877668057344145],
        [0.07661598914233601, 0.0, 0.0, -0.0018042105407654976, 0.12477201699512865, 0.0, -0.038383553414123014, -0.13518589408121312, 0.21018245422010579],
        [0.03650937782912379, 0.0, 0.0, -0.024334393960077933, 0.09154625092902843, 0.0, 0.0375423755906796, -0.0369424430932128, 0.12079544868468167],
    ],
    # The "color" dict lists indices {"0","1","3","5","6","8","9"} -- Stone &
    # Mountain in therefore only sample rows 0,1,3,5,6,8,9.
    "active": [0, 1, 3, 5, 6, 8, 9],
    "prob": [
        0.18173535415922157, 0.12693188009479223, 0.11203245756478104,
        0.10729577747369581, 0.10508095198299697, 0.08720755326805475,
        0.08547331599457036, 0.06928970489547422, 0.06438450615250647,
        0.060568498413906664,
    ],
}

def sample_mountain_soil_palette_color():
    """Draw a linear-RGBA colour from the mountain-soil JSON palette.

    ``n_sample=1`` and ``palette_name="mountain soil"``.
    """

    active = _PALETTE_MOUNTAIN_SOIL["active"]
    all_hsv = _PALETTE_MOUNTAIN_SOIL["hsv"]
    all_std = _PALETTE_MOUNTAIN_SOIL["std"]
    all_prob = _PALETTE_MOUNTAIN_SOIL["prob"]

    means_selected = [all_hsv[i] for i in active]
    stds_selected = [all_std[i] for i in active]
    probs_selected = np.array([all_prob[i] for i in active], dtype=float)
    probs_selected = probs_selected / probs_selected.sum()

    i = np.random.choice(np.arange(len(active)), 1, p=probs_selected)[0]
    mean = np.array(means_selected[i])
    std_mat = np.array(stds_selected[i]).reshape((3, 3))
    perturb = np.clip(np.random.randn(3), a_min=-1, a_max=1)
    hsv = mean + std_mat @ perturb
    hsv[2] = max(min(hsv[2], 0.9), 0.1)
    rgb = np.array(colorsys.hsv_to_rgb(float(hsv[0] % 1.0), float(np.clip(hsv[1], 0, 1)), float(hsv[2])))
    rgb = np.clip(rgb, 0, 1)
    rgb = np.where(rgb >= 0.04045, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)
    return (float(rgb[0]), float(rgb[1]), float(rgb[2]), 1.0)

# ─── shader_MOUNTAIN faithful replica ────────────────────────────────────────

def _add_z_layer_color_ramp(nt, link, tc_geom_out_0, z_min, z_max, num_layers, hue_diff):
    """Builds the layered Z->color ramp from shader_MOUNTAIN."""
    # Non-spherical branch: z = geometry.Position.z via SeparateXYZ
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    link(tc_geom_out_0, sep.inputs[0])  # Position
    map_range = nt.nodes.new("ShaderNodeMapRange")
    link(sep.outputs[2], map_range.inputs[0])

    z_noise_mag = float(np.random.uniform(0.1, 0.4))
    map_range.inputs[1].default_value = z_min
    map_range.inputs[2].default_value = z_max
    map_range.inputs[3].default_value = -1 * (z_noise_mag / 2)
    map_range.inputs[4].default_value = 1 - (z_noise_mag / 2)

    z_noise = nt.nodes.new("ShaderNodeTexNoise")
    link(tc_geom_out_0, z_noise.inputs["Vector"])
    z_noise.inputs["Scale"].default_value = 0.1
    z_noise.inputs["Detail"].default_value = 9
    z_noise_mul = nt.nodes.new("ShaderNodeMath")
    z_noise_mul.operation = "MULTIPLY"
    link(_fac_output(z_noise), z_noise_mul.inputs[0])
    z_noise_mul.inputs[1].default_value = float(np.random.uniform(0.1, 0.3))

    z_sum = nt.nodes.new("ShaderNodeMath")
    z_sum.operation = "ADD"
    link(map_range.outputs[0], z_sum.inputs[0])
    link(z_noise_mul.outputs[0], z_sum.inputs[1])

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    link(z_sum.outputs[0], ramp.inputs[0])

    # Build color ramp, emulating the loop from shader_MOUNTAIN
    elements = ramp.color_ramp.elements
    while len(elements) > 1:
        elements.remove(elements[0])

    cur_color = sample_mountain_soil_palette_color()
    elements[-1].color = cur_color

    prob_arranged_layers = 0.1
    # prior FixedSeed block already consumed uniform() for arranged_layers decision
    arranged_layers = _ARRANGED_LAYERS_FOR_MOUNTAIN

    cur_loc = 1.0
    for _ in range(num_layers):
        if arranged_layers:
            cur_loc -= float(np.random.uniform()) * 2.0 / num_layers
            cur_loc = max(0.0, cur_loc)
        else:
            cur_loc = float(np.random.uniform())
        element = elements.new(cur_loc)
        cur_color = sample_mountain_soil_palette_color()
        element.color = cur_color

    return ramp

_ARRANGED_LAYERS_FOR_MOUNTAIN = True

def make_mountain_material(name="MountainRock"):
    """Call order inside FixedSeed(random_seed=0):
      1. uniform() -> arranged_layers choice
      2. shader_roughness = rg(1)                  (deterministic constant)
      3. layered_mountain = rg(True)               (deterministic constant)
      4. per-z ramp: uniform(0.1,0.4) z_noise_mag
      5. uniform(0.1,0.3) z_noise scale
      6. palette sample 1    -> element[-1] color
      7. num_layers=16 times: uniform() + palette sample
    """

    global _ARRANGED_LAYERS_FOR_MOUNTAIN

    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new

    # FixedSeed(random_seed=0) -- the shader is deterministic at runtime.
    saved_state = (np.random.get_state(), random.getstate())
    np.random.seed(0)
    random.seed(0)
    try:
        prob_arranged_layers = 0.1
        if np.random.uniform() > prob_arranged_layers:
            _ARRANGED_LAYERS_FOR_MOUNTAIN = True
        else:
            _ARRANGED_LAYERS_FOR_MOUNTAIN = False

        shader_roughness = 1.0        # rg(1)
        layered_mountain = True       # rg(True)
        z_min, z_max = 0, 120         # preset_zrange
        num_layers = 16
        hue_diff = 0.1

        # GeometryNode for position + normal
        geom = nt.nodes.new("ShaderNodeNewGeometry")
        # Position output is index 0; Normal output is index 1
        ramp = _add_z_layer_color_ramp(
            nt, ln, geom.outputs[0], z_min, z_max, num_layers, hue_diff
        )

        # Ambient-occlusion shading factor
        amb_occl = nt.nodes.new("ShaderNodeAmbientOcclusion")
        ao_mix = nt.nodes.new("ShaderNodeMix"); ao_mix.data_type = "RGBA"
        ln(_fac_output(amb_occl), ao_mix.inputs[0])
        ao_mix.inputs[1].default_value = (0.0, 0.0, 0.0, 1.0)
        ln(ramp.outputs[0], ao_mix.inputs[2])
        layered_color = ao_mix  # this is the "ramp" in shader_MOUNTAIN after AO

        # normal.z shading attenuation:
        #   color_ = ramp * max(0.2, |(0,0,1) . normal|^3)
        # We build this in vector-math land because ShaderNodeMix won't accept
        # a scalar directly; final step is a vector multiply.
        geom_normal = nt.nodes.new("ShaderNodeNewGeometry")
        dot = nt.nodes.new("ShaderNodeVectorMath")
        dot.operation = "DOT_PRODUCT"
        dot.inputs[0].default_value = (0.0, 0.0, 1.0)
        ln(geom_normal.outputs["Normal"], dot.inputs[1])
        abs_node = nt.nodes.new("ShaderNodeMath")
        abs_node.operation = "ABSOLUTE"
        ln(dot.outputs["Value"], abs_node.inputs[0])
        pow_node = nt.nodes.new("ShaderNodeMath")
        pow_node.operation = "POWER"
        ln(abs_node.outputs[0], pow_node.inputs[0])
        pow_node.inputs[1].default_value = 3.0
        max_node = nt.nodes.new("ShaderNodeMath")
        max_node.operation = "MAXIMUM"
        max_node.inputs[0].default_value = 0.2
        ln(pow_node.outputs[0], max_node.inputs[1])

        color_mul = nt.nodes.new("ShaderNodeVectorMath")
        color_mul.operation = "MULTIPLY"
        ln(layered_color.outputs[0], color_mul.inputs[0])
        # Scalar fed through a "vector" input: connect to all 3 components
        scalar_to_vec = nt.nodes.new("ShaderNodeCombineXYZ")
        ln(max_node.outputs[0], scalar_to_vec.inputs[0])
        ln(max_node.outputs[0], scalar_to_vec.inputs[1])
        ln(max_node.outputs[0], scalar_to_vec.inputs[2])
        ln(scalar_to_vec.outputs[0], color_mul.inputs[1])

        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        ln(color_mul.outputs[0], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = shader_roughness
    finally:
        np.random.set_state(saved_state[0])
        random.setstate(saved_state[1])

    output = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs[0], output.inputs[0])
    return mat

# ─── shader_stone faithful replica ───────────────────────────────────────────

def make_stone_material(name="StoneRock"):
    """The geometry-side of ``geo_stone`` builds a vector displacement offset; the
    shader side (geometry=False) returns ``(base_color_ramp, roughness_ramp)``
    that drive the Principled BSDF.  Here we only need the colour/roughness
    chain that feeds the BSDF -- the displacement never reaches the shader.

    All randomness sits inside ``FixedSeed(random_seed=0)``.
    """

    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new

    saved_state = (np.random.get_state(), random.getstate())
    np.random.seed(0)
    random.seed(0)
    try:
        from numpy.random import normal as N
        from numpy.random import uniform as U

        # --- geo_stone scalar params (shader branch, geometry=False) ---
        size_bumps_lf = U(0, 30)
        heig_bumps_lf_v = U(0.08, 0.15)
        dens_crack = U(0, 0.1)
        scal_crack = U(5, 10) / 2
        widt_crack = U(0.08, 0.12)
        scale = 0.5

        # W values -- consumed but used only as 4D W seeds; Blender 5.0 noise
        # is 3D here because we don't need the 4D musgrave pipeline in shader
        # mode (original code passes them to 4D textures -- we mirror the
        # random-consumption order so downstream draws line up).
        _musgrave_w = U(0, 10)       # musgrave_texture_w
        _noise_tex_w = U(0, 10)      # noise_texture_w
        _noise_tex2_w = U(0, 10)     # noise_texture_2_w
        _noise_tex1_w = U(0, 10)     # noise_texture_1_w
        wave_tex_scale = N(2, 0.5)
        wave_tex_dist = N(6, 2)
        wave_tex_detail = N(15, 5)
        _noise_tex3_w = U(0, 10)
        noise_tex3_scale = 5 * float(np.exp(np.random.uniform(np.log(3 / 4), np.log(4 / 3))))
        _noise_tex4_w = U(0, 10)
        noise_tex4_scale = 20 * float(np.exp(np.random.uniform(np.log(3 / 4), np.log(4 / 3))))

        color1 = U(0, 0.05)
        color2 = U(0.05, 0.1)
        color3 = U(0, 0.05)

        rough_min = U(0.6, 0.7)
        rough_max = U(0.7, 0.8)

        # Shader nodes -----------------------------------------------------
        geom_pos = nt.nodes.new("ShaderNodeNewGeometry")
        position_out = geom_pos.outputs["Position"]

        # Musgrave-equivalent (Blender 5.0: use Noise texture, noise_dimensions '4D')
        musgrave = nt.nodes.new("ShaderNodeTexNoise")
        try:
            musgrave.noise_dimensions = "4D"
        except Exception:
            pass
        ln(position_out, musgrave.inputs["Vector"])
        musgrave.inputs["Scale"].default_value = float(size_bumps_lf) * scale
        if "W" in musgrave.inputs:
            musgrave.inputs["W"].default_value = float(_musgrave_w)
        musgrave.inputs["Detail"].default_value = 8.0
        musgrave.inputs["Roughness"].default_value = 0.5

        noise_tex = nt.nodes.new("ShaderNodeTexNoise")
        try:
            noise_tex.noise_dimensions = "4D"
        except Exception:
            pass
        ln(position_out, noise_tex.inputs["Vector"])
        noise_tex.inputs["Scale"].default_value = 12.0 * scale
        noise_tex.inputs["Detail"].default_value = 16.0
        if "W" in noise_tex.inputs:
            noise_tex.inputs["W"].default_value = float(_noise_tex_w)

        noise_tex2 = nt.nodes.new("ShaderNodeTexNoise")
        try:
            noise_tex2.noise_dimensions = "4D"
        except Exception:
            pass
        ln(position_out, noise_tex2.inputs["Vector"])
        noise_tex2.inputs["Scale"].default_value = 5.0 * scale
        if "W" in noise_tex2.inputs:
            noise_tex2.inputs["W"].default_value = float(_noise_tex2_w)

        # colorramp_2 -- dens_crack driven black/white ramp from noise_tex2.Fac
        cr2 = nt.nodes.new("ShaderNodeValToRGB")
        ln(_fac_output(noise_tex2), cr2.inputs[0])
        cr2.color_ramp.elements[0].position = 0.445 + (2 * float(dens_crack)) - 0.1
        cr2.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
        cr2.color_ramp.elements[1].position = 0.505 + (2 * float(dens_crack)) - 0.1
        cr2.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

        noise_tex1 = nt.nodes.new("ShaderNodeTexNoise")
        try:
            noise_tex1.noise_dimensions = "4D"
        except Exception:
            pass
        ln(position_out, noise_tex1.inputs["Vector"])
        noise_tex1.inputs["Scale"].default_value = 1.0 * scale
        noise_tex1.inputs["Detail"].default_value = 16.0
        if "W" in noise_tex1.inputs:
            noise_tex1.inputs["W"].default_value = float(_noise_tex1_w)

        wave_tex = nt.nodes.new("ShaderNodeTexWave")
        # Color output of NoiseTex drives Vector input of wave
        ln(noise_tex1.outputs["Color"], wave_tex.inputs["Vector"])
        wave_tex.inputs["Scale"].default_value = float(wave_tex_scale)
        wave_tex.inputs["Distortion"].default_value = float(wave_tex_dist)
        wave_tex.inputs["Detail"].default_value = float(wave_tex_detail)

        cr1 = nt.nodes.new("ShaderNodeValToRGB")
        ln(_fac_output(wave_tex), cr1.inputs[0])
        cr1.color_ramp.elements[0].position = 0.0
        cr1.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
        cr1.color_ramp.elements[1].position = float(widt_crack)
        cr1.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

        # mix = MixRGB(cr2.Color -> Fac, cr1.Color -> Color1)
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
        ln(cr2.outputs["Color"], mix.inputs[0])
        ln(cr1.outputs["Color"], mix.inputs[1])

        # colorramp -- base stone tone ramp driven by noise_tex.Fac
        cr_base = nt.nodes.new("ShaderNodeValToRGB")
        ln(_fac_output(noise_tex), cr_base.inputs[0])
        # Start with the two default stops, add a third.
        cr_base.color_ramp.elements.new(1)
        cr_base.color_ramp.elements[0].position = 0.223
        cr_base.color_ramp.elements[0].color = (float(color1), float(color1), float(color1), 1.0)
        cr_base.color_ramp.elements[1].position = 0.509
        # perturbs elements[1] and [2] with sample_color(offset=0.01).
        # We match by pushing a small random perturbation into hsv space.
        perturbed2 = list(colorsys.rgb_to_hsv(float(color2), float(color2), float(color2)))
        perturbed2[0] = (perturbed2[0] + float(np.random.uniform(-0.01, 0.01))) % 1.0
        perturbed2[1] = float(np.clip(perturbed2[1] + float(np.random.uniform(-0.01, 0.01)), 0, 1))
        perturbed2[2] = float(np.clip(perturbed2[2] + float(np.random.uniform(-0.01, 0.01)), 0, 1))
        p2_rgb = colorsys.hsv_to_rgb(*perturbed2)
        cr_base.color_ramp.elements[1].color = (p2_rgb[0], p2_rgb[1], p2_rgb[2], 1.0)
        cr_base.color_ramp.elements[2].position = 1.0
        perturbed3 = list(colorsys.rgb_to_hsv(float(color3), float(color3), float(color3)))
        perturbed3[0] = (perturbed3[0] + float(np.random.uniform(-0.01, 0.01))) % 1.0
        perturbed3[1] = float(np.clip(perturbed3[1] + float(np.random.uniform(-0.01, 0.01)), 0, 1))
        perturbed3[2] = float(np.clip(perturbed3[2] + float(np.random.uniform(-0.01, 0.01)), 0, 1))
        p3_rgb = colorsys.hsv_to_rgb(*perturbed3)
        cr_base.color_ramp.elements[2].color = (p3_rgb[0], p3_rgb[1], p3_rgb[2], 1.0)

        stone_base_color = nt.nodes.new("ShaderNodeMix"); stone_base_color.data_type = "RGBA"
        ln(mix.outputs[0], stone_base_color.inputs[0])
        stone_base_color.inputs[1].default_value = (0.0, 0.0, 0.0, 1.0)
        ln(cr_base.outputs["Color"], stone_base_color.inputs[2])

        # colorramp_3 -- roughness ramp driven by noise_tex.Fac
        cr_rough = nt.nodes.new("ShaderNodeValToRGB")
        ln(_fac_output(noise_tex), cr_rough.inputs[0])
        cr_rough.color_ramp.elements[0].position = 0.082
        cr_rough.color_ramp.elements[0].color = (float(rough_min), float(rough_min), float(rough_min), 1.0)
        cr_rough.color_ramp.elements[1].position = 0.768
        cr_rough.color_ramp.elements[1].color = (float(rough_max), float(rough_max), float(rough_max), 1.0)

        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        ln(stone_base_color.outputs[0], bsdf.inputs["Base Color"])
        ln(cr_rough.outputs["Color"], bsdf.inputs["Roughness"])
    finally:
        np.random.set_state(saved_state[0])
        random.setstate(saved_state[1])

    output = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs[0], output.inputs[0])
    return mat

# ─── rock registry: weighted sample (Mountain 5, Stone 1) ────────────────────

_ROCK_REGISTRY = [(make_mountain_material, 5), (make_stone_material, 1)]

def sample_rock_material(name):
    classes, weights = zip(*_ROCK_REGISTRY)
    weights = np.array(weights, dtype=float)
    fn = np.random.choice(classes, p=weights / weights.sum())
    return fn(name=name)

# ═════════════════════════════════════════════════════════════════════════════
# PHASE 1 -- sample on raw SEED, mirroring BoulderFactory.__init__
# ═════════════════════════════════════════════════════════════════════════════

_seed_all(SEED)
# 1) weighted_sample(material_assignments.rock)()  -> pick Mountain / Stone
# 2) np.random.choice(self.configs, p=self.weights) -> boulder vs slab (we pop
#    even though the geometry uses its own np.random.seed(seed) below).
CATEG_MAT = sample_rock_material("BoulderPileFactory_Material")
_ = np.random.choice(["boulder", "slab"], p=[0.8, 0.2])  # mirror draw order only
CATEG_MAT.use_fake_user = True

print(f"BoulderPileFactory: picked surface {CATEG_MAT.name}")

# ═════════════════════════════════════════════════════════════════════════════
# GEOMETRY -- copied verbatim from objects_blender/rocks/BoulderPileFactory.py
# ═════════════════════════════════════════════════════════════════════════════

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
        vl_objs = bpy.context.view_layer.objects
        for o in self.prev_sel or []:
            if o and o.name in vl_objs:
                o.select_set(True)
        if self.prev_active and self.prev_active.name in vl_objs:
            vl_objs.active = self.prev_active

def apply_transform(obj, loc=False, rot=True, scale=True):
    with SelectObjects(obj):
        bpy.ops.object.transform_apply(location=loc, rotation=rot, scale=scale)
    return obj

def apply_modifiers(obj):
    with SelectObjects(obj):
        for m in list(obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=m.name)
            except Exception:
                pass
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

def deep_clone_obj(obj, keep_modifiers=False, keep_materials=True):
    o = obj.copy()
    if obj.data:
        o.data = obj.data.copy()
    bpy.context.scene.collection.objects.link(o)
    if not keep_modifiers:
        for m in list(o.modifiers):
            try:
                o.modifiers.remove(m)
            except Exception:
                pass
    if not keep_materials and getattr(o.data, 'materials', None):
        o.data.materials.clear()
    for ch in obj.children:
        ch2 = deep_clone_obj(ch, keep_modifiers=keep_modifiers, keep_materials=keep_materials)
        ch2.parent = o
    return o

def join_objects(objs):
    objs = [o for o in objs if o is not None and o.name in bpy.data.objects]
    if not objs:
        return None
    with SelectObjects(objs, active=0):
        bpy.ops.object.join()
        return bpy.context.active_object

# ---- Convex hull mesh ----

def convex_hull_obj(vertices):
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
            [top_facing, nw.bernoulli(prob),
             nw.compare('GREATER_THAN', face_area, face_area_stats['Mean'])],
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
        input_kwargs={'Geometry': geometry, 'Name': 'top',
                      'Value': reduce(lambda *xs: nw.boolean_math('OR', *xs), tops)},
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

# ---- Create a single boulder ----

def create_boulder(is_slab=False):
    _select_none()
    vertices = np.random.uniform(-1, 1, (32, 3))
    obj = convex_hull_obj(vertices)
    add_geomod(obj, geo_extrusion, apply=True)
    modify_mesh(obj, 'SUBSURF', render_levels=2, levels=2, subdivision_type='SIMPLE')
    obj.location[2] += obj.dimensions[2] * 0.2
    apply_transform(obj, loc=True)
    if is_slab:
        obj.scale = *log_uniform(0.5, 2.0, 2), log_uniform(0.1, 0.15)
    else:
        obj.scale = *log_uniform(0.4, 1.2, 2), log_uniform(0.4, 0.8)
    apply_transform(obj)
    obj.rotation_euler[0] = uniform(-np.pi / 24, np.pi / 24)
    apply_transform(obj)
    obj.rotation_euler[2] = uniform(0, np.pi * 2)
    apply_transform(obj)
    with SelectObjects(obj):
        try:
            bpy.ops.geometry.attribute_convert(mode='VERTEX_GROUP')
        except Exception:
            pass
    if 'top' in obj.vertex_groups:
        modify_mesh(obj, 'BEVEL', limit_method='VGROUP', vertex_group='top',
                    invert_vertex_group=True, offset_type='PERCENT', width_pct=10)
    modify_mesh(obj, 'REMESH', mode='SHARP', octree_depth=3)
    add_geomod(obj, geo_extension, apply=True)
    for ns in [log_uniform(0.2, 0.5), log_uniform(0.05, 0.1)]:
        voronoi_tex = bpy.data.textures.new('boulder_voronoi', 'VORONOI')
        voronoi_tex.noise_scale = float(ns)
        voronoi_tex.distance_metric = 'DISTANCE'
        modify_mesh(obj, 'DISPLACE', texture=voronoi_tex, strength=0.01, mid_level=0)
    return obj

# ---- Build ----

def build(seed=0):
    np.random.seed(seed)

    is_slab = np.random.choice([False, True], p=[0.8, 0.2])
    n_groups = np.random.randint(3, 5)
    all_boulders = []

    for g in range(n_groups):
        boulder = create_boulder(is_slab)
        all_boulders.append(boulder)

        clone_scales = [
            log_uniform(0.4, 0.6),
            log_uniform(0.2, 0.4),
            log_uniform(0.2, 0.4),
            log_uniform(0.2, 0.4),
            log_uniform(0.1, 0.2),
        ]
        for s in clone_scales:
            clone = deep_clone_obj(boulder)
            clone.scale = [float(s)] * 3
            apply_transform(clone)
            all_boulders.append(clone)

    # Physics-based pile placement (matching original free_fall pipeline).
    r_floor = 4
    floor_res = 32
    floor_half = 12
    floor_verts = []
    floor_faces = []
    for iy in range(floor_res):
        for ix in range(floor_res):
            x = -floor_half + (2 * floor_half) * ix / (floor_res - 1)
            y = -floor_half + (2 * floor_half) * iy / (floor_res - 1)
            d = math.sqrt(x * x + y * y) - r_floor
            z = max(d, 0.01 * d)
            floor_verts.append((x, y, z))
    for iy in range(floor_res - 1):
        for ix in range(floor_res - 1):
            i0 = iy * floor_res + ix
            floor_faces.append((i0, i0 + 1, i0 + floor_res + 1, i0 + floor_res))
    floor_mesh = bpy.data.meshes.new('pile_floor')
    floor_mesh.from_pydata(floor_verts, [], floor_faces)
    floor_mesh.update()
    floor_obj = bpy.data.objects.new('pile_floor', floor_mesh)
    bpy.context.scene.collection.objects.link(floor_obj)

    all_boulders.sort(key=lambda o: -o.dimensions[-1])

    height = 0.0
    for b in all_boulders:
        b.location = (*uniform(-3, 3, 2), height)
        b.rotation_euler = (0, 0, uniform(0, np.pi * 2))
        height += b.dimensions[-1]

    bpy.context.view_layer.update()

    bpy.ops.rigidbody.world_add()
    for b in all_boulders:
        with SelectObjects(b):
            bpy.ops.rigidbody.objects_add(type='ACTIVE')
            bpy.ops.rigidbody.mass_calculate()
    with SelectObjects(floor_obj):
        bpy.ops.rigidbody.objects_add(type='PASSIVE')
        bpy.context.object.rigid_body.collision_shape = 'MESH'

    bpy.context.scene.frame_end = 100
    bpy.ops.ptcache.bake_all(bake=True)

    bpy.context.scene.frame_set(100)
    with SelectObjects(all_boulders):
        bpy.ops.object.visual_transform_apply()

    bpy.ops.rigidbody.world_remove()
    bpy.data.objects.remove(floor_obj, do_unlink=True)

    # Attach the rock material to every boulder BEFORE joining so the final
    # mesh ends up with a single rock material slot after join_objects.
    for b in all_boulders:
        if b and b.data is not None:
            b.data.materials.clear()
            b.data.materials.append(CATEG_MAT)

    obj = join_objects(all_boulders)

    # Multi-res (Catmull-Clark subdivision)
    try:
        mod = obj.modifiers.new('multires', 'MULTIRES')
        with SelectObjects(obj):
            bpy.ops.object.multires_subdivide(modifier=mod.name,
                                               mode='CATMULL_CLARK')
        apply_modifiers(obj)
    except Exception:
        pass

    # Voxel remesh
    modify_mesh(obj, 'REMESH', mode='VOXEL', voxel_size=0.005625)

    # Voxel remesh wipes material slots -> re-append so the joined mesh keeps
    # the single rock material after remeshing.
    if obj and obj.data is not None:
        obj.data.materials.clear()
        obj.data.materials.append(CATEG_MAT)

    obj.name = 'BoulderPileFactory'
    return obj

# ---- Main ----

bpy.context.scene.cursor.location = (0, 0, 0)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

result = build(SEED)
print(f"BoulderPileFactory built: {len(result.data.vertices)} verts, "
      f"{len(result.data.polygons)} faces, "
      f"{len(result.data.materials)} material slots")

