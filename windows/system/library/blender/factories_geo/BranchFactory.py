# [FL_INDEX: keywords="blender_factory, procedural_3d, BranchFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BranchFactory | Category: factories_geo
# Prompt: A 3D model of a leafy plant branch rendered from a slightly elevated perspective. The branch features a woody stem with multiple lateral offshoots, each bearing clusters of small ovate green leaves arranged along the length of the twigs.

"""BranchFactory (textured) — standalone Blender script.

Seeding: seed_all(int_hash((SEED,0))) for params/bark material,
         seed_all(int_hash((SEED,1))) for geometry. No FixedSeed resets.
Bark: BarkRandom (90%) or BarkBirch (10%).
"""


import os
import math
import random
import colorsys

import bpy
import bmesh
import numpy as np
from numpy.random import uniform, randint
from mathutils import Vector, noise as mnoise


SEED = int(os.environ.get("SEED", "0"))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)


def sel_none():
    for obj in list(bpy.context.selected_objects):
        obj.select_set(False)


def set_active(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


def apply_modifier(obj, mod):
    sel_none()
    set_active(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    sel_none()


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                  bpy.data.textures, bpy.data.images):
        for item in list(block):
            block.remove(item)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    bpy.context.scene.cursor.location = (0, 0, 0)


def read_co(obj):
    me = obj.data
    arr = np.zeros(len(me.vertices) * 3, dtype=np.float32)
    me.vertices.foreach_get("co", arr)
    return arr.reshape(-1, 3)


def int_hash(vals, mod=2**31 - 1):
    if isinstance(vals, (int, np.integer)):
        vals = (int(vals),)
    result = 0
    for v in vals:
        result = (result * 1000003 + int(v)) % mod
    return result


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

WOOD_COLORS = [
    0x4C2F27, 0x69432D, 0x371803, 0x7F4040, 0xCC9576, 0x9E8170, 0x3D2B1F,
    0x8D6A58, 0x8B3325, 0x79443C, 0x88540B, 0x9B5F43, 0x4E3828, 0x4E3828,
    0xC09A6B, 0x944536, 0x3F0110, 0x773C12, 0x6E4E37, 0x5C4033, 0x5C4033,
    0x3C3034, 0x96704C, 0x371B1A, 0x483B32, 0x43141A, 0x471713, 0xC3B090,
    0x6B4423, 0x674D46, 0x5D2E1A, 0x331C1F, 0x7A5640, 0xB99984, 0x71543D,
    0x8F4B28, 0x491A00, 0x836446, 0x7F461B, 0x6A3208, 0x724115, 0xA0522B,
    0x832A0C, 0x371B1A, 0xC7A373, 0x483B32, 0x635147, 0x664228, 0x5C5248,
]


def hex2rgb(hexval):
    r = ((hexval >> 16) & 0xFF) / 255.0
    g = ((hexval >> 8) & 0xFF) / 255.0
    b = (hexval & 0xFF) / 255.0
    return (r, g, b)


def bark_hsv():
    hexval = WOOD_COLORS[np.random.randint(len(WOOD_COLORS))]
    r, g, b = hex2rgb(hexval)
    return colorsys.rgb_to_hsv(r, g, b)


def hsv2rgba(h, s, v):
    h = h - math.floor(h)
    s = float(max(0.0, min(1.0, s)))
    v = float(max(0.0, min(1.0, v)))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def sample_branch_params():
    # Sample geo params in the same order as the geo-only version to keep
    # the RNG stream aligned.  Fruit params are textured-only additions and
    # must not consume draws from the main stream.
    params = {
        "resolution": 256,
        "main_branch_noise_amount": uniform(0.2, 0.4),
        "main_branch_noise_scale": uniform(0.9, 1.3),
        "overall_radius": uniform(0.015, 0.025),
        "twig_density": uniform(5, 15),
        "twig_rotation": uniform(30, 60),
        "twig_scale": uniform(3, 7),
        "twig_noise_amount": uniform(0.2, 0.4),
        "leaf_density": uniform(5, 25),
        "leaf_scale": uniform(0.25, 0.35),
        "leaf_rot": uniform(30, 60),
    }
    # Fruit params are extra draws that don't exist in the geo-only version.
    # Isolate them so the downstream RNG state matches.
    _state = np.random.get_state()
    params["fruit_scale"] = uniform(0.15, 0.25)
    params["fruit_rot"] = 0.0
    params["fruit_density"] = uniform(1, 5)
    np.random.set_state(_state)
    return params


# ---------------------------------------------------------------------------
# Bark material: BarkRandom (90% weight)
# shader_random_bark_mat + voronoi/noise coordinate pipeline
# ---------------------------------------------------------------------------

def create_bark_random_material(base_hsv=None):
    """BarkRandom shader: voronoi DISTANCE_TO_EDGE + noise, Z-stretched Object coords."""

    if base_hsv is None:
        base_hsv = bark_hsv()

    h, s, v = base_hsv

    # Sample geo_params like get_random_bark_params
    geo_z_noise_scale = np.random.uniform(1.0, 3.0)
    geo_z_noise_amount = np.random.uniform(0.5, 1.5)
    geo_z_multiplier = np.random.uniform(0.1, 0.3)
    geo_primary_voronoi_scale = np.random.uniform(20, 40)
    geo_primary_voronoi_randomness = np.random.uniform(0.6, 1.0)
    geo_secondary_voronoi_scale = np.random.uniform(30, 50)
    geo_noise_texture_scale = 15.0

    mat = bpy.data.materials.new("BarkRandom")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Output
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (1200, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (900, 0)
    bsdf.inputs["Roughness"].default_value = 0.7
    links.new(bsdf.outputs[0], output.inputs[0])

    # === Coordinate pipeline (approximates canonical coord) ===
    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-1200, 0)

    # Stretch Z to simulate the longitudinal bark grain
    sep_xyz = nodes.new("ShaderNodeSeparateXYZ")
    sep_xyz.location = (-1000, 0)
    links.new(tex_coord.outputs["Object"], sep_xyz.inputs["Vector"])

    z_multiply = nodes.new("ShaderNodeMath")
    z_multiply.location = (-800, -100)
    z_multiply.operation = "MULTIPLY"
    z_multiply.inputs[1].default_value = geo_z_multiplier * 10.0
    links.new(sep_xyz.outputs["Z"], z_multiply.inputs[0])

    # Add noise to Z (inject_z_noise_and_scale)
    z_noise = nodes.new("ShaderNodeTexNoise")
    z_noise.location = (-800, 100)
    z_noise.inputs["Scale"].default_value = geo_z_noise_scale
    links.new(tex_coord.outputs["Object"], z_noise.inputs["Vector"])

    z_noise_mul = nodes.new("ShaderNodeMath")
    z_noise_mul.location = (-600, 100)
    z_noise_mul.operation = "MULTIPLY"
    z_noise_mul.inputs[1].default_value = geo_z_noise_amount
    links.new(z_noise.outputs[0], z_noise_mul.inputs[0])

    z_add = nodes.new("ShaderNodeMath")
    z_add.location = (-600, -100)
    z_add.operation = "ADD"
    links.new(z_multiply.outputs[0], z_add.inputs[0])
    links.new(z_noise_mul.outputs[0], z_add.inputs[1])

    # Recombine into modified coordinate
    comb_xyz = nodes.new("ShaderNodeCombineXYZ")
    comb_xyz.location = (-400, 0)
    links.new(sep_xyz.outputs["X"], comb_xyz.inputs["X"])
    links.new(sep_xyz.outputs["Y"], comb_xyz.inputs["Y"])
    links.new(z_add.outputs[0], comb_xyz.inputs["Z"])

    # === Primary Voronoi (distance_to_edge) ===
    voronoi_primary = nodes.new("ShaderNodeTexVoronoi")
    voronoi_primary.location = (-200, 200)
    voronoi_primary.feature = "DISTANCE_TO_EDGE"
    voronoi_primary.inputs["Scale"].default_value = geo_primary_voronoi_scale
    voronoi_primary.inputs["Randomness"].default_value = geo_primary_voronoi_randomness
    links.new(comb_xyz.outputs["Vector"], voronoi_primary.inputs["Vector"])

    # map_range for primary voronoi: 0..1 -> 0..0.5
    mr_primary = nodes.new("ShaderNodeMapRange")
    mr_primary.location = (0, 200)
    mr_primary.inputs["To Max"].default_value = 0.5
    links.new(voronoi_primary.outputs["Distance"], mr_primary.inputs["Value"])

    # === Secondary Voronoi (for stripe detail) ===
    voronoi_secondary = nodes.new("ShaderNodeTexVoronoi")
    voronoi_secondary.location = (-200, -200)
    voronoi_secondary.feature = "DISTANCE_TO_EDGE"
    voronoi_secondary.inputs["Scale"].default_value = geo_secondary_voronoi_scale
    links.new(tex_coord.outputs["Object"], voronoi_secondary.inputs["Vector"])

    # map_range for secondary: 0..1 -> 0..0.5
    mr_secondary = nodes.new("ShaderNodeMapRange")
    mr_secondary.location = (0, -200)
    mr_secondary.inputs["To Max"].default_value = 0.5
    links.new(voronoi_secondary.outputs["Distance"], mr_secondary.inputs["Value"])

    # === Large noise layer (noise_texture_scale = 15) ===
    noise_large = nodes.new("ShaderNodeTexNoise")
    noise_large.location = (-200, -400)
    noise_large.inputs["Scale"].default_value = geo_noise_texture_scale
    noise_large.inputs["Detail"].default_value = 16.0
    links.new(tex_coord.outputs["Object"], noise_large.inputs["Vector"])

    # === Color chain (matches shader_random_bark_mat) ===
    # Base color from bark_hsv
    base_rgba = hsv2rgba(h, s, v)

    # Bright variant (V shift +0.1)
    bright_rgba = hsv2rgba(h, s, min(1.0, v + 0.1))
    # Dark variant (mix 0.1 with black)
    dark_r = bright_rgba[0] * 0.1
    dark_g = bright_rgba[1] * 0.1
    dark_b = bright_rgba[2] * 0.1

    # mix_3: Fac=primary_voronoi, Color1=dark_mix, Color2=bright
    mix3 = nodes.new("ShaderNodeMix")
    mix3.location = (200, 200)
    mix3.data_type = "RGBA"
    mix3.inputs[6].default_value = (dark_r, dark_g, dark_b, 1.0)
    mix3.inputs[7].default_value = bright_rgba
    links.new(mr_primary.outputs["Result"], mix3.inputs[0])

    # mix_0: Fac=secondary_voronoi map (0..0.7), Color1=mix3, Color2=dark_mix
    mr_secondary_color = nodes.new("ShaderNodeMapRange")
    mr_secondary_color.location = (0, -100)
    mr_secondary_color.inputs["To Max"].default_value = 0.7
    links.new(mr_secondary.outputs["Result"], mr_secondary_color.inputs["Value"])

    mix0 = nodes.new("ShaderNodeMix")
    mix0.location = (400, 100)
    mix0.data_type = "RGBA"
    links.new(mr_secondary_color.outputs["Result"], mix0.inputs[0])
    links.new(mix3.outputs[2], mix0.inputs[6])
    mix0.inputs[7].default_value = (dark_r, dark_g, dark_b, 1.0)

    # mix_1: noise-based light accent (0.9 * white + bright)
    accent_rgba = (
        0.9 * 1.0 + 0.1 * bright_rgba[0],
        0.9 * 1.0 + 0.1 * bright_rgba[1],
        0.9 * 1.0 + 0.1 * bright_rgba[2],
        1.0,
    )

    # Noise fac for accent spots (noise_texture * 2 scale)
    noise_accent = nodes.new("ShaderNodeTexNoise")
    noise_accent.location = (-200, -600)
    noise_accent.inputs["Scale"].default_value = geo_noise_texture_scale * 2.0
    links.new(tex_coord.outputs["Object"], noise_accent.inputs["Vector"])

    mr_accent = nodes.new("ShaderNodeMapRange")
    mr_accent.location = (0, -600)
    mr_accent.inputs["From Min"].default_value = 0.35
    mr_accent.inputs["From Max"].default_value = 0.4
    mr_accent.inputs["To Min"].default_value = 0.5
    mr_accent.inputs["To Max"].default_value = 0.0
    links.new(noise_accent.outputs[0], mr_accent.inputs["Value"])

    mix1 = nodes.new("ShaderNodeMix")
    mix1.location = (600, 0)
    mix1.data_type = "RGBA"
    links.new(mr_accent.outputs["Result"], mix1.inputs[0])
    links.new(mix0.outputs[2], mix1.inputs[6])
    mix1.inputs[7].default_value = accent_rgba

    # mix_2: noise-based dark spots (noise_texture * 4 scale)
    noise_dark = nodes.new("ShaderNodeTexNoise")
    noise_dark.location = (-200, -800)
    noise_dark.inputs["Scale"].default_value = geo_noise_texture_scale * 4.0
    links.new(tex_coord.outputs["Object"], noise_dark.inputs["Vector"])

    mr_dark = nodes.new("ShaderNodeMapRange")
    mr_dark.location = (0, -800)
    mr_dark.inputs["From Min"].default_value = 0.35
    mr_dark.inputs["From Max"].default_value = 0.4
    mr_dark.inputs["To Min"].default_value = 0.5
    mr_dark.inputs["To Max"].default_value = 0.0
    links.new(noise_dark.outputs[0], mr_dark.inputs["Value"])

    dark_spot_rgba = (
        0.9 * 0.0 + 0.1 * bright_rgba[0],
        0.9 * 0.0 + 0.1 * bright_rgba[1],
        0.9 * 0.0 + 0.1 * bright_rgba[2],
        1.0,
    )

    mix2 = nodes.new("ShaderNodeMix")
    mix2.location = (750, 0)
    mix2.data_type = "RGBA"
    links.new(mr_dark.outputs["Result"], mix2.inputs[0])
    links.new(mix1.outputs[2], mix2.inputs[6])
    mix2.inputs[7].default_value = dark_spot_rgba

    links.new(mix2.outputs[2], bsdf.inputs["Base Color"])

    # === Bump from voronoi + noise (bark surface detail) ===
    # Primary voronoi for large-scale bark ridges
    bump_voronoi = nodes.new("ShaderNodeTexVoronoi")
    bump_voronoi.location = (200, -400)
    bump_voronoi.feature = "DISTANCE_TO_EDGE"
    bump_voronoi.inputs["Scale"].default_value = geo_primary_voronoi_scale
    bump_voronoi.inputs["Randomness"].default_value = geo_primary_voronoi_randomness
    links.new(comb_xyz.outputs["Vector"], bump_voronoi.inputs["Vector"])

    bump1 = nodes.new("ShaderNodeBump")
    bump1.location = (500, -400)
    bump1.inputs["Strength"].default_value = 0.35
    bump1.inputs["Distance"].default_value = 0.015
    links.new(bump_voronoi.outputs["Distance"], bump1.inputs["Height"])

    # Fine detail noise bump
    bump_noise_fine = nodes.new("ShaderNodeTexNoise")
    bump_noise_fine.location = (200, -600)
    bump_noise_fine.inputs["Scale"].default_value = 60.0
    bump_noise_fine.inputs["Detail"].default_value = 8.0
    links.new(tex_coord.outputs["Object"], bump_noise_fine.inputs["Vector"])

    bump2 = nodes.new("ShaderNodeBump")
    bump2.location = (700, -400)
    bump2.inputs["Strength"].default_value = 0.15
    bump2.inputs["Distance"].default_value = 0.005
    links.new(bump_noise_fine.outputs[0], bump2.inputs["Height"])
    links.new(bump1.outputs[0], bump2.inputs["Normal"])

    links.new(bump2.outputs[0], bsdf.inputs["Normal"])

    return mat


# ---------------------------------------------------------------------------
# Bark material: BarkBirch (10% weight)
# ---------------------------------------------------------------------------

def create_bark_birch_material():
    """BarkBirch shader: musgrave + stripe noise, white/cream bark with dark patches."""

    mat = bpy.data.materials.new("BarkBirch")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (800, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (500, 0)
    links.new(bsdf.outputs[0], output.inputs[0])

    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-800, 0)

    # Stretch Z for bark grain
    sep = nodes.new("ShaderNodeSeparateXYZ")
    sep.location = (-600, 0)
    links.new(tex_coord.outputs["Object"], sep.inputs["Vector"])

    z_mul = nodes.new("ShaderNodeMath")
    z_mul.location = (-400, -100)
    z_mul.operation = "MULTIPLY"
    z_mul.inputs[1].default_value = 10.0
    links.new(sep.outputs["Z"], z_mul.inputs[0])

    comb = nodes.new("ShaderNodeCombineXYZ")
    comb.location = (-200, 0)
    links.new(sep.outputs["X"], comb.inputs["X"])
    links.new(sep.outputs["Y"], comb.inputs["Y"])
    links.new(z_mul.outputs[0], comb.inputs["Z"])

    # Noise for stripe pattern (match birch_mat_helper)
    noise1 = nodes.new("ShaderNodeTexNoise")
    noise1.location = (0, 200)
    noise1.inputs["Scale"].default_value = 50.0
    noise1.inputs["Detail"].default_value = 10.0
    links.new(tex_coord.outputs["Object"], noise1.inputs["Vector"])

    mr_noise1 = nodes.new("ShaderNodeMapRange")
    mr_noise1.location = (200, 200)
    mr_noise1.inputs["From Min"].default_value = 0.3
    mr_noise1.inputs["From Max"].default_value = 0.4
    mr_noise1.inputs["To Min"].default_value = 1.0
    mr_noise1.inputs["To Max"].default_value = 0.0
    links.new(noise1.outputs[0], mr_noise1.inputs["Value"])

    # Stretched noise for R,G,B channels -> stripe detection
    noise2 = nodes.new("ShaderNodeTexNoise")
    noise2.location = (0, -100)
    noise2.inputs["Scale"].default_value = 2.0
    links.new(comb.outputs["Vector"], noise2.inputs["Vector"])

    # Separate R channel for stripe
    sep_rgb = nodes.new("ShaderNodeSeparateColor")
    sep_rgb.location = (200, -100)
    links.new(noise2.outputs["Color"], sep_rgb.inputs["Color"])

    mr_stripe = nodes.new("ShaderNodeMapRange")
    mr_stripe.location = (400, -100)
    mr_stripe.inputs["From Min"].default_value = 0.341
    mr_stripe.inputs["From Max"].default_value = 0.377
    links.new(sep_rgb.outputs[0], mr_stripe.inputs["Value"])

    # Musgrave-like large scale pattern (use noise as approximation)
    noise_musgrave = nodes.new("ShaderNodeTexNoise")
    noise_musgrave.location = (0, -300)
    noise_musgrave.inputs["Scale"].default_value = 2.0
    noise_musgrave.inputs["Detail"].default_value = 10.0
    noise_musgrave.inputs["Roughness"].default_value = 0.6
    links.new(tex_coord.outputs["Object"], noise_musgrave.inputs["Vector"])

    mr_musgrave = nodes.new("ShaderNodeMapRange")
    mr_musgrave.location = (200, -300)
    mr_musgrave.inputs["From Min"].default_value = 0.3
    mr_musgrave.inputs["From Max"].default_value = 0.5
    links.new(noise_musgrave.outputs[0], mr_musgrave.inputs["Value"])

    power = nodes.new("ShaderNodeMath")
    power.location = (400, -300)
    power.operation = "POWER"
    power.use_clamp = True
    power.inputs[1].default_value = 0.2
    links.new(mr_musgrave.outputs["Result"], power.inputs[0])

    # Color mixing chain (birch: dark greens/browns + cream)
    # Dark bark color
    dark_color = (0.0252, 0.0395, 0.0176, 1.0)
    # Medium bark
    medium_color = (0.0823, 0.1095, 0.0595, 1.0)
    # Light (cream/brown)
    cream_color = (0.0437, 0.0482, 0.0222, 1.0)
    # Dark brown
    dark_brown = (0.0232, 0.0144, 0.0021, 1.0)

    # mix1: stripe -> dark bark vs medium
    mix1 = nodes.new("ShaderNodeMix")
    mix1.location = (600, -100)
    mix1.data_type = "RGBA"
    mix1.inputs[6].default_value = medium_color
    mix1.inputs[7].default_value = dark_brown
    links.new(power.outputs[0], mix1.inputs[0])

    # mix2: noise1 detail -> mix1 vs cream
    mix2 = nodes.new("ShaderNodeMix")
    mix2.location = (800, 0)
    mix2.data_type = "RGBA"
    links.new(mr_noise1.outputs["Result"], mix2.inputs[0])
    links.new(mix1.outputs[2], mix2.inputs[6])
    mix2.inputs[7].default_value = cream_color

    links.new(mix2.outputs[2], bsdf.inputs["Base Color"])

    # Roughness from musgrave pattern
    mr_rough = nodes.new("ShaderNodeMapRange")
    mr_rough.location = (400, -500)
    mr_rough.inputs["To Max"].default_value = 0.4
    links.new(power.outputs[0], mr_rough.inputs["Value"])
    links.new(mr_rough.outputs["Result"], bsdf.inputs["Roughness"])

    # Bump from stripe noise
    bump = nodes.new("ShaderNodeBump")
    bump.location = (600, -400)
    bump.inputs["Strength"].default_value = 0.3
    bump.inputs["Distance"].default_value = 0.01
    links.new(mr_stripe.outputs["Result"], bump.inputs["Height"])
    links.new(bump.outputs[0], bsdf.inputs["Normal"])

    return mat


def create_leaf_material():
    """Simple green material for leaf placeholders."""

    mat = bpy.data.materials.new("LeafGreen")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (400, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (100, 0)
    # Random green leaf
    leaf_hue = np.random.uniform(0.22, 0.38)
    leaf_sat = np.random.uniform(0.4, 0.8)
    leaf_val = np.random.uniform(0.15, 0.45)
    bsdf.inputs["Base Color"].default_value = hsv2rgba(leaf_hue, leaf_sat, leaf_val)
    bsdf.inputs["Roughness"].default_value = 0.6
    links.new(bsdf.outputs[0], output.inputs[0])

    return mat


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def create_bark_material():
    """Select bark material with weights: BarkRandom 90%, BarkBirch 10%."""

    if np.random.uniform() < 0.1:
        return create_bark_birch_material()
    else:
        return create_bark_random_material()


# ---------------------------------------------------------------------------
# Branch geometry (translated from generate_branch GeoNodes)
# ---------------------------------------------------------------------------

def make_curve_points(resolution, seed, noise_amount, noise_scale):
    """Create main branch as array of 3D points along a noisy line.

    Matches: CurveLine -> ResampleCurve -> noise SetPosition
    The branch goes from (0,0,0) to (0,0,1) with noise displacement.
    """

    points = np.zeros((resolution, 3), dtype=np.float64)
    for i in range(resolution):
        t = i / max(1, resolution - 1)
        # Base position along Y axis (branch direction, rotated later)
        base = np.array([0.0, t, 0.0])

        # Noise displacement (matches 2D noise with vector=CombineXYZ(X=t, Y=seed))
        noise_coord = Vector((t * noise_scale, seed / 1e7, 0.0))
        nval = mnoise.noise(noise_coord)
        # Subtract 0.5 and scale by envelope
        envelope = min(1.0, t / 0.2)  # MapRange: t -> 0..0.2 mapped to 0..1
        offset_x = (nval - 0.5) * envelope * noise_amount * 0.5
        offset_z = (mnoise.noise(noise_coord + Vector((17.3, 0, 0))) - 0.5) * envelope * noise_amount * 0.5

        points[i] = base + np.array([offset_x, 0.0, offset_z])

    return points


def make_twig_points(resolution, seed, noise_amount):
    """Create a single twig sub-branch as array of 3D points.

    Matches: CurveLine(End=(0,0,0.1)) -> ResampleCurve(Count=res/2) -> noise
    """

    n_pts = max(4, resolution // 2)
    points = np.zeros((n_pts, 3), dtype=np.float64)
    for i in range(n_pts):
        t = i / max(1, n_pts - 1)
        base = np.array([0.0, t * 0.1, 0.0])

        noise_coord = Vector((t * 1.5, seed / 1e7, 0.0))
        nval = mnoise.noise(noise_coord)
        envelope = min(1.0, t / 0.2)
        offset_x = (nval - 0.5) * envelope * noise_amount * 0.3
        offset_z = (mnoise.noise(noise_coord + Vector((31.7, 0, 0))) - 0.5) * envelope * noise_amount * 0.3

        points[i] = base + np.array([offset_x, 0.0, offset_z])

    return points


def points_to_tube(points, radius_func, profile_res=8):
    """Convert a polyline to a tube mesh (like CurveToMesh with CurveCircle).

    radius_func(t) returns the radius at parameter t in [0, 1].
    """

    n_pts = len(points)
    if n_pts < 2:
        return [], []

    verts = []
    faces = []

    for i in range(n_pts):
        t = i / max(1, n_pts - 1)
        r = radius_func(t)

        # Compute tangent
        if i == 0:
            tangent = points[1] - points[0]
        elif i == n_pts - 1:
            tangent = points[-1] - points[-2]
        else:
            tangent = points[i + 1] - points[i - 1]
        tangent = tangent / (np.linalg.norm(tangent) + 1e-10)

        # Build local frame
        up = np.array([0.0, 0.0, 1.0])
        if abs(np.dot(tangent, up)) > 0.99:
            up = np.array([1.0, 0.0, 0.0])
        right = np.cross(tangent, up)
        right = right / (np.linalg.norm(right) + 1e-10)
        up = np.cross(right, tangent)
        up = up / (np.linalg.norm(up) + 1e-10)

        # Circle vertices
        for j in range(profile_res):
            angle = 2.0 * math.pi * j / profile_res
            offset = r * (math.cos(angle) * right + math.sin(angle) * up)
            verts.append(tuple(points[i] + offset))

    # Faces: quad strips between rings
    for i in range(n_pts - 1):
        for j in range(profile_res):
            j_next = (j + 1) % profile_res
            v0 = i * profile_res + j
            v1 = i * profile_res + j_next
            v2 = (i + 1) * profile_res + j_next
            v3 = (i + 1) * profile_res + j
            faces.append((v0, v1, v2, v3))

    return verts, faces


def make_leaf_mesh(leaf_length=0.08, leaf_width=0.04, res_along=20, res_across=10,
                   midrib_depth=0.003, curl_amount=0.005, name="leaf"):
    """Parametric broadleaf mesh aligned to objects_blender BranchFactory leaves."""

    verts = []
    for i in range(res_along):
        t = i / max(res_along - 1, 1)
        y = t * leaf_length
        if t < 0.15:
            w_frac = (t / 0.15) ** 2 * 0.06
        elif t < 0.93:
            t_norm = (t - 0.15) / 0.78
            w_frac = math.sin(t_norm * math.pi) ** 0.65
        else:
            w_frac = max(0.0, 1.0 - (t - 0.93) / 0.07) * 0.15

        half_w = leaf_width * 0.5 * max(w_frac, 0.0)
        for j in range(res_across):
            s = j / max(res_across - 1, 1) - 0.5
            x = s * 2.0 * half_w
            x_norm = abs(s) * 2.0
            z_midrib = midrib_depth * math.exp(-5.0 * x_norm ** 2) * (0.3 + 0.7 * t)
            vein_phase = t * 7.0 + x_norm * 3.5
            z_vein = (
                midrib_depth * 0.15 * math.exp(-2.5 * x_norm ** 2)
                * max(0.0, math.sin(vein_phase * math.pi))
            )
            z_cup = -curl_amount * 0.3 * (s * 2.0) ** 2
            verts.append((x, y, z_midrib + z_vein + z_cup))

    faces = []
    for i in range(res_along - 1):
        for j in range(res_across - 1):
            v0 = i * res_across + j
            faces.append((v0, v0 + 1, v0 + res_across + 1, v0 + res_across))

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(obj.data)
    bm.free()

    sel_none()
    set_active(obj)
    sub = obj.modifiers.new("sub", "SUBSURF")
    sub.levels = 2
    sub.render_levels = 2
    bpy.ops.object.modifier_apply(modifier=sub.name)

    sol = obj.modifiers.new("sol", "SOLIDIFY")
    sol.thickness = 0.0006
    sol.offset = 0
    bpy.ops.object.modifier_apply(modifier=sol.name)
    sel_none()
    return obj


def create_branch_mesh(params, seed):
    """Build the full branch geometry: main trunk + twigs + leaves + fruit.

    """
    # Use same seed as geo-only version (np.random.seed(seed) already called
    # before param sampling; continue from that state rather than re-seeding
    # with int_hash which would produce different branch_seed values).

    resolution = params["resolution"]
    noise_amount = params["main_branch_noise_amount"]
    noise_scale = params["main_branch_noise_scale"]
    overall_radius = params["overall_radius"]
    twig_density = params["twig_density"]
    twig_rotation_deg = params["twig_rotation"]
    twig_scale = params["twig_scale"]
    twig_noise_amount = params["twig_noise_amount"]
    leaf_density = params["leaf_density"]
    leaf_scale = params["leaf_scale"]
    leaf_rot_deg = params["leaf_rot"]
    fruit_scale = params["fruit_scale"]
    fruit_density = params["fruit_density"]

    all_objects = []

    # --- Main branch curve ---
    branch_seed = np.random.randint(10000000)
    main_pts = make_curve_points(resolution, branch_seed, noise_amount, noise_scale)

    # Radius: MapRange(t, 0..1 -> 1..0.4) * overall_radius
    def main_radius(t):
        envelope = 1.0 - t * 0.6  # 1.0 at base, 0.4 at tip
        return envelope * overall_radius

    main_verts, main_faces = points_to_tube(main_pts, main_radius, profile_res=12)

    if main_verts:
        mesh = bpy.data.meshes.new("MainBranch")
        mesh.from_pydata(main_verts, [], main_faces)
        mesh.update()
        obj = bpy.data.objects.new("MainBranch", mesh)
        bpy.context.scene.collection.objects.link(obj)
        all_objects.append(obj)

    # --- Twig sub-branches ---
    n_twigs = max(1, int(twig_density * 0.3))  # keep probability 0.3
    twig_start_t = 0.05
    twig_end_t = 0.9

    for ti in range(n_twigs):
        t = twig_start_t + (twig_end_t - twig_start_t) * (ti + np.random.uniform(0, 0.5)) / n_twigs
        if t > twig_end_t:
            continue

        # Base position on main branch
        idx = int(t * (len(main_pts) - 1))
        idx = max(0, min(idx, len(main_pts) - 1))
        base_pos = main_pts[idx]

        # Tangent at this point
        if idx < len(main_pts) - 1:
            tangent = main_pts[min(idx + 1, len(main_pts) - 1)] - main_pts[idx]
        else:
            tangent = main_pts[idx] - main_pts[max(0, idx - 1)]
        tangent = tangent / (np.linalg.norm(tangent) + 1e-10)

        # Twig direction: rotate away from tangent
        # Use a separate RandomState per twig instead of re-seeding global state,
        # so the global stream stays aligned with the geo-only version.
        twig_seed = int_hash((branch_seed, ti, 37))
        _twig_rng = np.random.RandomState(twig_seed)

        # Random rotation around tangent
        rot_around = _twig_rng.uniform(0, 2 * math.pi)
        rot_angle = math.radians(twig_rotation_deg * _twig_rng.uniform(0.8, 1.2))

        # Build rotation frame
        up = np.array([0.0, 0.0, 1.0])
        if abs(np.dot(tangent, up)) > 0.99:
            up = np.array([1.0, 0.0, 0.0])
        right = np.cross(tangent, up)
        right = right / (np.linalg.norm(right) + 1e-10)
        up_dir = np.cross(right, tangent)
        up_dir = up_dir / (np.linalg.norm(up_dir) + 1e-10)

        # Twig direction: rotated from tangent
        twig_dir = (
            tangent * math.cos(rot_angle)
            + (math.cos(rot_around) * right + math.sin(rot_around) * up_dir) * math.sin(rot_angle)
        )
        twig_dir = twig_dir / (np.linalg.norm(twig_dir) + 1e-10)

        # Scale by envelope (larger twigs near base)
        scale_envelope = 1.0 - t * 0.9  # tapers from 1 at base to 0.1 at tip
        twig_len = 0.1 * twig_scale * scale_envelope * 0.15

        twig_pts = make_twig_points(resolution, twig_seed, twig_noise_amount)
        # Transform twig points into world space
        # Original twig is along Y; we need to orient along twig_dir
        for pi in range(len(twig_pts)):
            local = twig_pts[pi].copy()
            # Scale
            local *= twig_len / 0.1  # normalize from 0.1 length
            # Orient: Y -> twig_dir
            y_axis = np.array([0.0, 1.0, 0.0])
            # Simple rotation from y to twig_dir
            fwd = twig_dir
            side = np.cross(fwd, up_dir)
            side_norm = np.linalg.norm(side)
            if side_norm > 1e-6:
                side = side / side_norm
            up2 = np.cross(side, fwd)
            # Transform: local.x -> side, local.y -> fwd, local.z -> up2
            world_pt = base_pos + local[0] * side + local[1] * fwd + local[2] * up2
            twig_pts[pi] = world_pt

        # Twig radius
        twig_r = overall_radius * scale_envelope * 0.4

        def twig_radius(t_param, base_r=twig_r):
            return base_r * (1.0 - t_param * 0.8)

        tv, tf = points_to_tube(twig_pts, twig_radius, profile_res=6)
        if tv:
            tmesh = bpy.data.meshes.new(f"Twig_{ti}")
            tmesh.from_pydata(tv, [], tf)
            tmesh.update()
            tobj = bpy.data.objects.new(f"Twig_{ti}", tmesh)
            bpy.context.scene.collection.objects.link(tobj)
            all_objects.append(tobj)

            # --- Leaves along twig ---
            n_leaves = max(1, int(leaf_density * 0.3 * scale_envelope))
            for li in range(n_leaves):
                leaf_t = np.random.uniform(0.1, 1.0)
                leaf_idx = int(leaf_t * (len(twig_pts) - 1))
                leaf_idx = max(0, min(leaf_idx, len(twig_pts) - 1))
                leaf_pos = twig_pts[leaf_idx]

                leaf_length = float(np.random.uniform(0.20, 0.30)) * leaf_scale
                leaf_width = leaf_length * float(np.random.uniform(0.45, 0.60))
                leaf_obj = make_leaf_mesh(
                    leaf_length=leaf_length,
                    leaf_width=leaf_width,
                    midrib_depth=float(np.random.uniform(0.003, 0.006)) * leaf_scale,
                    curl_amount=float(np.random.uniform(0.003, 0.008)) * leaf_scale,
                    name=f"Leaf_{ti}_{li}",
                )
                leaf_obj.location = tuple(leaf_pos)
                # Random rotation
                leaf_obj.rotation_euler = (
                    np.random.uniform(-0.5, 0.5) + math.radians(leaf_rot_deg),
                    np.random.uniform(-0.3, 0.3),
                    np.random.uniform(0, 2 * math.pi),
                )
                all_objects.append(leaf_obj)

    # --- Fruit along main branch ---
    n_fruits = max(0, int(fruit_density * 0.3))
    for fi in range(n_fruits):
        fruit_t = np.random.uniform(0.2, 0.9)
        fruit_idx = int(fruit_t * (len(main_pts) - 1))
        fruit_idx = max(0, min(fruit_idx, len(main_pts) - 1))
        fruit_pos = main_pts[fruit_idx]

        bpy.ops.mesh.primitive_ico_sphere_add(
            radius=fruit_scale * 0.02,
            location=tuple(fruit_pos),
        )
        fruit_obj = bpy.context.active_object
        fruit_obj.name = f"Fruit_{fi}"
        all_objects.append(fruit_obj)

    return all_objects


def apply_surface_bump(obj, displacement=0.005, scale=50.0):
    """Apply noise-based surface bump (matches nodegroup_surface_bump).

    Uses vertex displacement via bmesh since this is simpler than GeoNodes
    in standalone scripts.
    """

    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()

    bump_seed = np.random.uniform(0, 100)
    for v in bm.verts:
        noise_co = Vector((v.co.x * scale, v.co.y * scale, v.co.z * scale + bump_seed))
        nval = mnoise.noise(noise_co)
        offset = (nval - 0.5) * displacement
        v.co += v.normal * offset

    bm.to_mesh(me)
    bm.free()
    me.update()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    clear_scene()

    seed = SEED
    seed_all(seed)

    params = sample_branch_params()

    # Create bark material (weighted: 90% random, 10% birch)
    # Isolate material RNG draws so they don't shift geometry params
    _rng_state = np.random.get_state()
    _py_state = random.getstate()
    seed_all(int_hash((seed, 0)))
    bark_mat = create_bark_material()
    leaf_mat = create_leaf_material()
    np.random.set_state(_rng_state)
    random.setstate(_py_state)

    # Build geometry with RNG state continuing from param sampling
    objects = create_branch_mesh(params, seed)

    # Apply materials and surface bump
    for obj in objects:
        sel_none()
        set_active(obj)

        if "Leaf" in obj.name:
            obj.data.materials.append(leaf_mat)
        elif "Fruit" in obj.name:
            # Dark reddish fruit
            fruit_mat = bpy.data.materials.new(f"FruitMat_{obj.name}")
            fruit_mat.use_nodes = True
            fruit_nodes = fruit_mat.node_tree.nodes
            fruit_bsdf = fruit_nodes.get("Principled BSDF")
            if fruit_bsdf:
                fruit_bsdf.inputs["Base Color"].default_value = hsv2rgba(
                    np.random.uniform(0.0, 0.1),
                    np.random.uniform(0.5, 0.9),
                    np.random.uniform(0.2, 0.5),
                )
                fruit_bsdf.inputs["Roughness"].default_value = 0.5
            obj.data.materials.append(fruit_mat)
        else:
            # Branch/twig: apply bark material and surface bump
            obj.data.materials.append(bark_mat)
            apply_surface_bump(obj, displacement=0.005, scale=50.0)

    # This rotates the branch from Y-up to Z-up orientation
    for obj in objects:
        obj.rotation_euler[0] += -math.pi / 2

    # Apply transforms
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.transform_apply(rotation=True)
    sel_none()

    print(f"BranchFactory: created {len(objects)} objects (seed={seed})")


if __name__ == "__main__":
    main()
