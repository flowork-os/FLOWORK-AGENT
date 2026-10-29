# [FL_INDEX: keywords="blender_factory, procedural_3d, BlenderRockFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BlenderRockFactory | Category: factories_geo
# Prompt: A 3D model of a natural rock rendered from a slightly elevated three-quarter perspective. The rock features a compact, irregularly shaped form with layered, rough surface ridges and crevices, a flat-bottomed base, and a gray stone coloring with subtle lighter and darker tonal variation across its weathered surface.

"""
Standalone Blender script (geometry + rock material) – BlenderRockFactory.

Geometry: icosphere + multi-layer DISPLACE textures + SUBSURF, copied verbatim
from objects_blender/rocks/BlenderRockFactory.py.

  (terrain.Mountain, 5), (terrain.Stone, 1)
Both shaders are translated faithfully from
into raw bpy node-tree construction. No wear_tear (pebbles.py / blender_rock.py
do not apply scratches/edge-wear to rocks).
"""


import os
import math
import random
import colorsys

import bpy
import numpy as np


SEED = int(os.environ.get("SEED", "0"))
# SEED-deterministic: _seed_all(SEED) called at module level for material; np.random.seed(seed) in build()

# =============================================================================
# Helper utilities
# =============================================================================

def _seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)


def _new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat


def _fac_out(node):
    return node.outputs.get("Fac") or node.outputs.get("Factor") or node.outputs[0]


def _srgb_to_linear(c):
    return c ** 2.4 if c >= 0.04045 else c / 12.92


# =============================================================================
# Palette sampler — faithful port of sample_json_palette("mountain soil")
# =============================================================================

_MOUNTAIN_SOIL_HSV = [
    [0.07657200610458859, 0.6218981568424602, 0.568095301296071],
    [0.08871291011143334, 0.42452686112786103, 0.8104250687813854],
    [0.6140700215233733,  0.13288612784624504, 0.8730243901503021],
    [0.47346124527783656, 0.22768637564378527, 0.28529322850725286],
    [0.5961218425011782,  0.49810503051093324, 0.7223871831892953],
    [0.14544462943019612, 0.5389329914616029,  0.29703170640400595],
    [0.12202185913813124, 0.49872400694381797, 0.614810311196337],
    [0.02216908447486423, 0.027253574342521403, 0.9994307999673898],
    [0.13984012270413265, 0.20105405545965413, 0.6344186455983115],
    [0.0620713740714641,  0.8670860688594698,  0.3201029563817151],
]

_MOUNTAIN_SOIL_STD = [
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
]

_MOUNTAIN_SOIL_PROB = [
    0.18173535415922157, 0.12693188009479223, 0.11203245756478104,
    0.10729577747369581, 0.10508095198299697, 0.08720755326805475,
    0.08547331599457036, 0.06928970489547422, 0.06438450615250647,
    0.060568498413906664,
]


def sample_mountain_soil():
    means = np.array(_MOUNTAIN_SOIL_HSV)
    stds = np.array(_MOUNTAIN_SOIL_STD)
    probs = np.array(_MOUNTAIN_SOIL_PROB)
    i = np.random.choice(range(len(probs)), 1, p=probs / probs.sum())[0]
    hsv = np.array(means[i]) + np.matmul(
        np.array(stds[i]).reshape((3, 3)),
        np.clip(np.random.randn(3), a_min=-1, a_max=1),
    )
    hsv[2] = max(min(hsv[2], 0.9), 0.1)
    rgb = np.array(colorsys.hsv_to_rgb(*hsv))
    rgb = np.clip(rgb, 0.0, 1.0)
    # sRGB -> linear, matching sample_json_palette
    rgb = np.array([_srgb_to_linear(float(c)) for c in rgb])
    return (float(rgb[0]), float(rgb[1]), float(rgb[2]), 1.0)


# =============================================================================
# shader_MOUNTAIN translation (is_rock=True, layered=True, no snow)
# =============================================================================

def make_mountain_material(name="RockMountainMaterial"):
    mat = _new_material(name)
    nt = mat.node_tree
    link = nt.links.new

    # FixedSeed inside shader_MOUNTAIN normally resets to random_seed=0, but we
    # want per-SEED diversity — caller seeds numpy before calling us.
    prob_arranged_layers = 0.1
    arranged_layers = (np.random.uniform() > prob_arranged_layers)
    shader_roughness = 1.0          # rg(shader_roughness) with default 1
    num_layers = 16

    # --- z coordinate → map range → noise perturb → color ramp -------------
    tex_coor = nt.nodes.new("ShaderNodeNewGeometry")

    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    link(tex_coor.outputs["Position"], sep.inputs["Vector"])

    z_map = nt.nodes.new("ShaderNodeMapRange")
    link(sep.outputs["Z"], z_map.inputs[0])

    z_noise_mag = float(np.random.uniform(0.1, 0.4))
    preset_zrange = (0, 120)   # is_rock/spherical=False default
    z_min, z_max = preset_zrange
    z_map.inputs[1].default_value = float(z_min)
    z_map.inputs[2].default_value = float(z_max)
    z_map.inputs[3].default_value = -1.0 * (z_noise_mag / 2.0)
    z_map.inputs[4].default_value = 1.0 - (z_noise_mag / 2.0)

    z_noise = nt.nodes.new("ShaderNodeTexNoise")
    link(tex_coor.outputs["Position"], z_noise.inputs["Vector"])
    z_noise.inputs["Scale"].default_value = 0.1
    z_noise.inputs["Detail"].default_value = 9.0

    z_noise_mul = nt.nodes.new("ShaderNodeMath")
    z_noise_mul.operation = "MULTIPLY"
    link(_fac_out(z_noise), z_noise_mul.inputs[0])
    z_noise_mul.inputs[1].default_value = float(np.random.uniform(0.1, 0.3))

    z_add = nt.nodes.new("ShaderNodeMath")
    z_add.operation = "ADD"
    link(z_map.outputs["Result"], z_add.inputs[0])
    link(z_noise_mul.outputs["Value"], z_add.inputs[1])

    # --- color ramp with 16 layers from mountain-soil palette --------------
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    link(z_add.outputs["Value"], ramp.inputs["Fac"])
    elements = ramp.color_ramp.elements
    # Replace the default two elements with a single starting element then add layers
    elements.remove(elements[0])
    elements[-1].color = sample_mountain_soil()

    cur_loc = 1.0
    for _ in range(num_layers):
        if arranged_layers:
            cur_loc -= float(np.random.uniform()) * 2.0 / num_layers
            cur_loc = max(0.0, cur_loc)
        else:
            cur_loc = float(np.random.uniform())
        element = elements.new(cur_loc)
        element.color = sample_mountain_soil()

    # --- ambient occlusion multiply ----------------------------------------
    amb_occl = nt.nodes.new("ShaderNodeAmbientOcclusion")
    ao_mix = nt.nodes.new("ShaderNodeMixRGB")
    link(_fac_out(amb_occl), ao_mix.inputs["Fac"])
    ao_mix.inputs["Color1"].default_value = (0.0, 0.0, 0.0, 1.0)
    link(ramp.outputs["Color"], ao_mix.inputs["Color2"])

    # --- angle-of-normal darkening: max(0.2, |dot((0,0,1), N)|^3) ----------
    # Source mountain.py uses VectorMath DOT_PRODUCT (→ scalar "Value"), then
    # VectorMath ABSOLUTE (implicit scalar→vector broadcast), then scalar POWER.
    # Do the whole chain in scalar math to avoid version-dependent type quirks.
    geom_for_normal = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[0].default_value = (0.0, 0.0, 1.0)
    link(geom_for_normal.outputs["Normal"], dot.inputs[1])

    abs_dot = nt.nodes.new("ShaderNodeMath")
    abs_dot.operation = "ABSOLUTE"
    link(dot.outputs["Value"], abs_dot.inputs[0])

    power3 = nt.nodes.new("ShaderNodeMath")
    power3.operation = "POWER"
    link(abs_dot.outputs["Value"], power3.inputs[0])
    power3.inputs[1].default_value = 3.0

    max_02 = nt.nodes.new("ShaderNodeMath")
    max_02.operation = "MAXIMUM"
    max_02.inputs[0].default_value = 0.2
    link(power3.outputs["Value"], max_02.inputs[1])

    color_scale = nt.nodes.new("ShaderNodeVectorMath")
    color_scale.operation = "MULTIPLY"
    link(ao_mix.outputs["Color"], color_scale.inputs[0])
    # VectorMath accepts scalar via component broadcast — wrap into a vector
    combine = nt.nodes.new("ShaderNodeCombineXYZ")
    link(max_02.outputs["Value"], combine.inputs[0])
    link(max_02.outputs["Value"], combine.inputs[1])
    link(max_02.outputs["Value"], combine.inputs[2])
    link(combine.outputs["Vector"], color_scale.inputs[1])

    # --- Principled BSDF ---------------------------------------------------
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    link(color_scale.outputs["Vector"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = shader_roughness

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    link(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# =============================================================================
# shader_stone translation (surface only, no geometry displacement)
# =============================================================================

def _sample_ratio(x, lo=0.5, hi=2.0):
    if x == 0:
        return x
    neg = -1 if x < 0 else 1
    x = abs(x)
    exp = random.uniform(math.log(x * lo), math.log(x * hi))
    return neg * math.exp(exp)


def make_stone_material(name="RockStoneMaterial"):
    mat = _new_material(name)
    nt = mat.node_tree
    link = nt.links.new

    # Parameters sampled exactly like shader_stone/geo_stone (geometry=False) ---
    size_bumps_lf = float(np.random.uniform(0, 30))
    heig_bumps_lf_val = float(np.random.uniform(0.08, 0.15))
    dens_crack = float(np.random.uniform(0, 0.1))
    scal_crack = float(np.random.uniform(5, 10)) / 2.0
    widt_crack = float(np.random.uniform(0.08, 0.12))
    scale = 0.5

    # Additional parameter draws matching the shader_stone call order
    musgrave_w = float(np.random.uniform(0, 10))
    noise_texture_w = float(np.random.uniform(0, 10))
    noise_texture_2_w = float(np.random.uniform(0, 10))
    noise_texture_1_w = float(np.random.uniform(0, 10))
    wave_scale = float(np.random.normal(2, 0.5))
    wave_distortion = float(np.random.normal(6, 2))
    wave_detail = float(np.random.normal(15, 5))
    noise_texture_3_w = float(np.random.uniform(0, 10))
    noise_texture_3_scale = _sample_ratio(5.0, 3.0 / 4.0, 4.0 / 3.0)
    noise_texture_4_scale = _sample_ratio(20.0, 3.0 / 4.0, 4.0 / 3.0)
    noise_texture_4_w = float(np.random.uniform(0, 10))
    color1 = float(np.random.uniform(0, 0.05))
    color2 = float(np.random.uniform(0.05, 0.1))
    color3 = float(np.random.uniform(0, 0.05))
    # sample_color offsets (two calls in source — consume RNG to stay aligned)
    _ = [random.uniform(-0.01, 0.01) for _ in range(3)]
    _ = [random.uniform(-0.01, 0.01) for _ in range(3)]
    rough_min = float(np.random.uniform(0.6, 0.7))
    rough_max = float(np.random.uniform(0.7, 0.8))

    # --- position source (shader graph uses NewGeometry.Position) -----------
    position_node = nt.nodes.new("ShaderNodeNewGeometry")
    position_out = position_node.outputs["Position"]

    # --- Musgrave replacement (Blender 5.0): ShaderNodeTexNoise ------------
    # Original: MusgraveTexture 4D with Scale=size_bumps_lf*scale, W=musgrave_w
    musgrave = nt.nodes.new("ShaderNodeTexNoise")
    musgrave.noise_dimensions = "4D"
    link(position_out, musgrave.inputs["Vector"])
    musgrave.inputs["Scale"].default_value = size_bumps_lf * scale
    if "W" in musgrave.inputs:
        musgrave.inputs["W"].default_value = musgrave_w

    # noise_texture (4D): Scale 12*scale, Detail 16
    noise_texture = nt.nodes.new("ShaderNodeTexNoise")
    noise_texture.noise_dimensions = "4D"
    link(position_out, noise_texture.inputs["Vector"])
    noise_texture.inputs["Scale"].default_value = 12.0 * scale
    noise_texture.inputs["Detail"].default_value = 16.0
    if "W" in noise_texture.inputs:
        noise_texture.inputs["W"].default_value = noise_texture_w

    # noise_texture_2 (4D): Scale 5*scale
    noise_texture_2 = nt.nodes.new("ShaderNodeTexNoise")
    noise_texture_2.noise_dimensions = "4D"
    link(position_out, noise_texture_2.inputs["Vector"])
    noise_texture_2.inputs["Scale"].default_value = 5.0 * scale
    if "W" in noise_texture_2.inputs:
        noise_texture_2.inputs["W"].default_value = noise_texture_2_w

    # colorramp_2 — black-to-white crack mask driven by dens_crack
    colorramp_2 = nt.nodes.new("ShaderNodeValToRGB")
    link(_fac_out(noise_texture_2), colorramp_2.inputs["Fac"])
    colorramp_2.color_ramp.elements[0].position = 0.445 + (2 * dens_crack) - 0.1
    colorramp_2.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    colorramp_2.color_ramp.elements[1].position = 0.505 + (2 * dens_crack) - 0.1
    colorramp_2.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # noise_texture_1 (4D): Scale 1*scale, Detail 16 — used as Vector for Wave
    noise_texture_1 = nt.nodes.new("ShaderNodeTexNoise")
    noise_texture_1.noise_dimensions = "4D"
    link(position_out, noise_texture_1.inputs["Vector"])
    noise_texture_1.inputs["Scale"].default_value = 1.0 * scale
    noise_texture_1.inputs["Detail"].default_value = 16.0
    if "W" in noise_texture_1.inputs:
        noise_texture_1.inputs["W"].default_value = noise_texture_1_w

    wave_texture = nt.nodes.new("ShaderNodeTexWave")
    # Wave Vector takes the Color output of the noise
    link(noise_texture_1.outputs["Color"], wave_texture.inputs["Vector"])
    wave_texture.inputs["Scale"].default_value = wave_scale
    wave_texture.inputs["Distortion"].default_value = wave_distortion
    wave_texture.inputs["Detail"].default_value = wave_detail

    colorramp_1 = nt.nodes.new("ShaderNodeValToRGB")
    link(_fac_out(wave_texture), colorramp_1.inputs["Fac"])
    colorramp_1.color_ramp.elements[0].position = 0.0
    colorramp_1.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    colorramp_1.color_ramp.elements[1].position = widt_crack
    colorramp_1.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # mix (MixRGB): Fac=colorramp_2.Color, Color1=colorramp_1.Color (Color2 default)
    mix = nt.nodes.new("ShaderNodeMixRGB")
    link(colorramp_2.outputs["Color"], mix.inputs["Fac"])
    link(colorramp_1.outputs["Color"], mix.inputs["Color1"])

    # --- Base Color: MixRGB(Fac=mix, Color1=black, Color2=colorramp) -------
    colorramp = nt.nodes.new("ShaderNodeValToRGB")
    link(_fac_out(noise_texture), colorramp.inputs["Fac"])
    # Replace default 2 elements with 3 stops: positions 0.223, 0.509, 1.0
    colorramp.color_ramp.elements.new(1)
    # offset color values by +/-0.01 for slight per-seed variation
    def _perturbed(v):
        return max(0.0, min(1.0, v + (random.random() - 0.5) * 2 * 0.01))
    c1 = color1
    c2 = _perturbed(color2)
    c3 = _perturbed(color3)
    colorramp.color_ramp.elements[0].position = 0.223
    colorramp.color_ramp.elements[0].color = (c1, c1, c1, 1.0)
    colorramp.color_ramp.elements[1].position = 0.509
    colorramp.color_ramp.elements[1].color = (c2, c2, c2, 1.0)
    colorramp.color_ramp.elements[2].position = 1.0
    colorramp.color_ramp.elements[2].color = (c3, c3, c3, 1.0)

    stone_base_color = nt.nodes.new("ShaderNodeMixRGB")
    link(mix.outputs["Color"], stone_base_color.inputs["Fac"])
    stone_base_color.inputs["Color1"].default_value = (0.0, 0.0, 0.0, 1.0)
    link(colorramp.outputs["Color"], stone_base_color.inputs["Color2"])

    # --- Roughness: colorramp_3 driven by noise_texture.Fac ----------------
    colorramp_3 = nt.nodes.new("ShaderNodeValToRGB")
    link(_fac_out(noise_texture), colorramp_3.inputs["Fac"])
    colorramp_3.color_ramp.elements[0].position = 0.082
    colorramp_3.color_ramp.elements[0].color = (rough_min, rough_min, rough_min, 1.0)
    colorramp_3.color_ramp.elements[1].position = 0.768
    colorramp_3.color_ramp.elements[1].color = (rough_max, rough_max, rough_max, 1.0)

    # --- Principled BSDF ---------------------------------------------------
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    link(stone_base_color.outputs["Color"], bsdf.inputs["Base Color"])
    link(colorramp_3.outputs["Color"], bsdf.inputs["Roughness"])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    link(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# =============================================================================
# Registry — weighted pick matching material_assignments.rock
# =============================================================================

REGISTRY_ROCK = [
    (make_mountain_material, 5.0),
    (make_stone_material,    1.0),
]


def weighted_sample(reg):
    classes, weights = zip(*reg)
    weights = np.array(weights, dtype=float)
    idx = int(np.random.choice(len(classes), p=weights / weights.sum()))
    return classes[idx]


# =============================================================================
# =============================================================================

_seed_all(SEED)
_mat_fn = weighted_sample(REGISTRY_ROCK)
CATEG_MAT = _mat_fn(name="BlenderRockFactory_Material")
CATEG_MAT.use_fake_user = True

# No WEAR_DO_SCRATCH / WEAR_DO_EDGEWEAR flags needed.


# =============================================================================
# Geometry helpers (copied verbatim from objects_blender/rocks/BlenderRockFactory.py)
# =============================================================================

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

def apply_modifiers(obj):
    with SelectObjects(obj):
        for m in list(obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=m.name)
            except Exception:
                pass
    return obj

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


# Displacement layers: (texture_type, noise_scale, strength_multiplier)
_DISPLACEMENT_LAYERS = [
    ('VORONOI', 0.8, 0.15),
    ('CLOUDS',  0.5, 0.08),
    ('VORONOI', 0.3, 0.04),
]

def _create_rock(zscale_range, rough):
    """Create a rock mesh: icosphere + multi-layer displacement."""

    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=4, radius=0.5, location=(0, 0, 0),
    )
    obj = bpy.context.active_object

    z0, z1 = zscale_range
    obj.scale = (1.0, 1.0, np.random.uniform(z0, z1))
    apply_transform(obj)

    for tex_type, noise_scale, strength_mult in _DISPLACEMENT_LAYERS:
        tex = bpy.data.textures.new('rock_disp', tex_type)
        tex.noise_scale = noise_scale
        modify_mesh(obj, 'DISPLACE', texture=tex, strength=rough * strength_mult, mid_level=0.5)
        bpy.data.textures.remove(tex)

    modify_mesh(obj, 'SUBSURF', levels=1, render_levels=1)
    return obj


# =============================================================================
# Build
# =============================================================================

def build(seed=SEED):
    # Geometry uses its own re-seed — materials are already captured above.
    np.random.seed(seed)

    zscale = np.random.uniform(0.2, 0.8)
    zrand = np.random.uniform(0, 0.7)
    rough = np.random.uniform(0.5, 1.0)

    obj = _create_rock(
        zscale_range=(zrand * zscale, zscale),
        rough=rough,
    )
    bpy.ops.object.shade_flat()
    apply_modifiers(obj)
    obj.name = "BlenderRockFactory"

    # Bind the single rock material (no per-part multi-material for rocks).
    obj.data.materials.clear()
    obj.data.materials.append(CATEG_MAT)

    return obj


# =============================================================================
# Main
# =============================================================================

bpy.context.scene.cursor.location = (0, 0, 0)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

build(SEED)
