# [FL_INDEX: keywords="blender_factory, procedural_3d, SucculentFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: SucculentFactory | Category: factories_tex
# Prompt: A 3D model of a succulent plant rendered from an elevated three-quarter perspective, featuring a compact rosette of thick fleshy overlapping petals arranged in concentric layers, with small protruding filaments at the center, colored in soft pale pink with subtle surface detail.

import os, math, random, colorsys
import bpy
import numpy as np
from numpy.random import normal, randint, uniform

# ── Seed helpers ──────────────────────────────────────────────────────────
SEED = int(os.environ.get('SEED', 0))

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)

# ── Scene cleanup ─────────────────────────────────────────────────────────
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
for ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(ng)
for mat in list(bpy.data.materials):
    bpy.data.materials.remove(mat)
bpy.context.scene.cursor.location = (0, 0, 0)

# ══════════════════════════════════════════════════════════════════════════
# Inlined material library — hand-crafted for SucculentFactory
# Five shaders: green_transition, pink_transition, green, yellow, whitish_green
# ══════════════════════════════════════════════════════════════════════════

def _hsv2rgba(hsv):
    """Convert HSV tuple to RGBA,"""

    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def _noise_fac_output(noise_node):
    """Get the Fac/Factor output from a noise texture node (Blender 4.x/5.0 compat)."""

    return noise_node.outputs.get("Fac") or noise_node.outputs[0]

def _make_noise_musgrave_substitute(nt, scale):
    """Create a Noise Texture node as substitute for removed Musgrave.
    Returns the node."""

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 2.0
    return noise

def _build_base_perturbation_chain(nt, noise_scale, less_than_threshold, multiply_factor):
    """Build the common Musgrave -> ColorRamp -> LessThan(Z) -> Multiply -> Multiply chain.

    Returns (multiply_1_output, separate_xyz_node) for downstream use.
    This pattern is shared by all 5 succulent shaders.
    """
    # Noise (substitute for Musgrave)
    noise = _make_noise_musgrave_substitute(nt, noise_scale)

    # ColorRamp: black at 0.1182, white at 0.7727
    color_ramp = nt.nodes.new("ShaderNodeValToRGB")
    color_ramp.color_ramp.elements[0].position = 0.1182
    color_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    color_ramp.color_ramp.elements[1].position = 0.7727
    color_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    nt.links.new(_noise_fac_output(noise), color_ramp.inputs[0])

    # TextureCoord -> Mapping -> SeparateXYZ
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])

    sep_xyz = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(mapping.outputs["Vector"], sep_xyz.inputs["Vector"])

    # LessThan(Z, threshold)
    less_than = nt.nodes.new("ShaderNodeMath")
    less_than.operation = "LESS_THAN"
    less_than.inputs[1].default_value = less_than_threshold
    nt.links.new(sep_xyz.outputs["Z"], less_than.inputs[0])

    # Multiply(ColorRamp, LessThan)
    mul_0 = nt.nodes.new("ShaderNodeMath")
    mul_0.operation = "MULTIPLY"
    nt.links.new(color_ramp.outputs["Color"], mul_0.inputs[0])
    nt.links.new(less_than.outputs[0], mul_0.inputs[1])

    # Multiply(above, factor)
    mul_1 = nt.nodes.new("ShaderNodeMath")
    mul_1.operation = "MULTIPLY"
    nt.links.new(mul_0.outputs[0], mul_1.inputs[0])
    mul_1.inputs[1].default_value = multiply_factor

    return mul_1, sep_xyz

def make_green_transition_succulent(name="GreenTransitionSucculent"):
    noise_scale = float(uniform(5.0, 20.0))
    mul_factor = float(uniform(2.0, 10.0))

    main_hsv_color = (float(uniform(0.35, 0.42)), float(uniform(0.5, 0.93)), float(uniform(0.20, 0.80)))
    main_color = _hsv2rgba(main_hsv_color)
    diffuse_color = _hsv2rgba((float(uniform(0.34, 0.43)),) + main_hsv_color[1:])
    split_point = float(uniform(0.82, 0.92))
    tip_color_r = float(uniform(0.6, 1.0))
    tip_color_g = float(uniform(0.0, 0.08))
    tip_color_b = float(uniform(0.0, 0.08))
    tip_color = (tip_color_r, tip_color_g, tip_color_b, 1.0)
    subsurface_weight = float(uniform(0.01, 0.03))
    diffuse_roughness = float(uniform(0.3, 0.8))

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    mul_1, sep_xyz = _build_base_perturbation_chain(nt, noise_scale, 0.85, mul_factor)

    # Z-based color ramp: main_color -> tip_color at split_point
    z_ramp = nt.nodes.new("ShaderNodeValToRGB")
    z_ramp.color_ramp.interpolation = "B_SPLINE"
    z_ramp.color_ramp.elements[0].position = split_point
    z_ramp.color_ramp.elements[0].color = main_color
    z_ramp.color_ramp.elements[1].position = split_point + float(uniform(0.01, 0.05))
    z_ramp.color_ramp.elements[1].color = tip_color
    nt.links.new(sep_xyz.outputs["Z"], z_ramp.inputs[0])

    # Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(z_ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Subsurface Weight"].default_value = subsurface_weight
    bsdf.inputs["Subsurface Radius"].default_value = (0.01, 0.1, 0.1)
    # Subsurface Color = same as base color (removed in Blender 5.0)
    if "Subsurface Color" in bsdf.inputs:
        nt.links.new(z_ramp.outputs["Color"], bsdf.inputs["Subsurface Color"])
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.0
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 2.0
    if "Coat Roughness" in bsdf.inputs:
        bsdf.inputs["Coat Roughness"].default_value = 0.0
    bsdf.inputs["IOR"].default_value = 1.3
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = 0.0

    # Diffuse BSDF
    diffuse_bsdf = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diffuse_bsdf.inputs["Color"].default_value = diffuse_color
    diffuse_bsdf.inputs["Roughness"].default_value = diffuse_roughness

    # MixShader(mul_1, principled, diffuse)
    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mul_1.outputs[0], mix_shader.inputs[0])
    nt.links.new(bsdf.outputs[0], mix_shader.inputs[1])
    nt.links.new(diffuse_bsdf.outputs[0], mix_shader.inputs[2])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mix_shader.outputs[0], out.inputs["Surface"])
    return mat

def make_pink_transition_succulent(name="PinkTransitionSucculent"):
    noise_scale = float(uniform(5.0, 20.0))
    mul_factor = float(uniform(2.0, 8.0))

    main_hsv_color = (float(uniform(0.93, 0.99)), float(uniform(0.64, 0.90)), float(uniform(0.50, 0.90)))
    main_color = _hsv2rgba(main_hsv_color)
    diffuse_color = _hsv2rgba((float(uniform(0.93, 1.0)),) + main_hsv_color[1:])
    split_point = float(uniform(0.82, 0.92))
    subsurface_weight = float(uniform(0.01, 0.05))
    diffuse_roughness = float(uniform(0.0, 0.5))

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    mul_1, sep_xyz = _build_base_perturbation_chain(nt, noise_scale, 0.85, mul_factor)

    # Z-based color ramp: main_color -> (no explicit second color in original = remains default)
    z_ramp = nt.nodes.new("ShaderNodeValToRGB")
    z_ramp.color_ramp.interpolation = "B_SPLINE"
    z_ramp.color_ramp.elements[0].position = split_point
    z_ramp.color_ramp.elements[0].color = main_color
    z_ramp.color_ramp.elements[1].position = split_point + float(uniform(0.01, 0.05))
    # Pink shader: element[1] color not explicitly set in original (default white stays)
    nt.links.new(sep_xyz.outputs["Z"], z_ramp.inputs[0])

    # Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(z_ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Subsurface Weight"].default_value = subsurface_weight
    bsdf.inputs["Subsurface Radius"].default_value = (0.01, 0.03, 0.03)
    if "Subsurface Color" in bsdf.inputs:
        nt.links.new(z_ramp.outputs["Color"], bsdf.inputs["Subsurface Color"])
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.0
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 2.0
    if "Coat Roughness" in bsdf.inputs:
        bsdf.inputs["Coat Roughness"].default_value = 0.0
    bsdf.inputs["IOR"].default_value = 1.3
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = 0.0

    # Diffuse BSDF
    diffuse_bsdf = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diffuse_bsdf.inputs["Color"].default_value = diffuse_color
    diffuse_bsdf.inputs["Roughness"].default_value = diffuse_roughness

    # MixShader
    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mul_1.outputs[0], mix_shader.inputs[0])
    nt.links.new(bsdf.outputs[0], mix_shader.inputs[1])
    nt.links.new(diffuse_bsdf.outputs[0], mix_shader.inputs[2])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mix_shader.outputs[0], out.inputs["Surface"])
    return mat

def make_green_succulent(name="GreenSucculent"):
    noise_scale = float(uniform(4.0, 15.0))
    mul_factor = float(uniform(2.0, 8.0))

    main_hsv_color = (float(uniform(0.33, 0.39)), float(uniform(0.5, 0.93)), float(uniform(0.20, 0.70)))
    main_color = _hsv2rgba(main_hsv_color)
    diffuse_color = _hsv2rgba((float(uniform(0.34, 0.38)),) + main_hsv_color[1:])
    diffuse_roughness = float(uniform(0.0, 0.5))
    subsurface_weight = float(uniform(0.01, 0.05))

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    mul_1, sep_xyz = _build_base_perturbation_chain(nt, noise_scale, 1.0, mul_factor)

    # Z-based color ramp: single color (position=1.0 means just the main color everywhere)
    z_ramp = nt.nodes.new("ShaderNodeValToRGB")
    z_ramp.color_ramp.interpolation = "B_SPLINE"
    z_ramp.color_ramp.elements[0].position = 1.0
    z_ramp.color_ramp.elements[0].color = main_color
    nt.links.new(sep_xyz.outputs["Z"], z_ramp.inputs[0])

    # Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(z_ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Subsurface Weight"].default_value = subsurface_weight
    bsdf.inputs["Subsurface Radius"].default_value = (0.1, 0.1, 0.1)
    if "Subsurface Color" in bsdf.inputs:
        nt.links.new(z_ramp.outputs["Color"], bsdf.inputs["Subsurface Color"])
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.0
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 2.0
    if "Coat Roughness" in bsdf.inputs:
        bsdf.inputs["Coat Roughness"].default_value = 0.0
    bsdf.inputs["IOR"].default_value = 1.3
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = 0.0

    # Diffuse BSDF
    diffuse_bsdf = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diffuse_bsdf.inputs["Color"].default_value = diffuse_color
    diffuse_bsdf.inputs["Roughness"].default_value = diffuse_roughness

    # MixShader
    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mul_1.outputs[0], mix_shader.inputs[0])
    nt.links.new(bsdf.outputs[0], mix_shader.inputs[1])
    nt.links.new(diffuse_bsdf.outputs[0], mix_shader.inputs[2])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mix_shader.outputs[0], out.inputs["Surface"])
    return mat

def make_yellow_succulent(name="YellowSucculent"):
    noise_scale = float(uniform(5.0, 8.0))
    mul_factor = float(uniform(1.0, 3.0))

    main_color = _hsv2rgba((float(uniform(0.1, 0.15)), float(uniform(0.8, 1.0)), float(uniform(0.5, 0.7))))
    tip_color = _hsv2rgba((float(uniform(0.0, 0.06)), float(uniform(0.8, 1.0)), float(uniform(0.5, 0.7))))
    diffuse_roughness = float(uniform(0.2, 1.0))

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    mul_1, sep_xyz = _build_base_perturbation_chain(nt, noise_scale, 1.0, mul_factor)

    # Z-based color ramp: main_color at 0.3114, tip_color at 0.6864
    z_ramp = nt.nodes.new("ShaderNodeValToRGB")
    z_ramp.color_ramp.interpolation = "B_SPLINE"
    z_ramp.color_ramp.elements[0].position = 0.3114
    z_ramp.color_ramp.elements[0].color = main_color
    z_ramp.color_ramp.elements[1].position = 0.6864
    z_ramp.color_ramp.elements[1].color = tip_color
    nt.links.new(sep_xyz.outputs["Z"], z_ramp.inputs[0])

    # Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(z_ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Subsurface Weight"].default_value = 0.01
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 1.0, 1.0)
    # Subsurface Color = combine(Alpha, Alpha, Alpha) from z_ramp
    # In the original, nw.combine(*([colorramp_1.outputs["Alpha"]] * 3))
    if "Subsurface Color" in bsdf.inputs:
        combine_sub = nt.nodes.new("ShaderNodeCombineXYZ")
        nt.links.new(z_ramp.outputs["Alpha"], combine_sub.inputs[0])
        nt.links.new(z_ramp.outputs["Alpha"], combine_sub.inputs[1])
        nt.links.new(z_ramp.outputs["Alpha"], combine_sub.inputs[2])
        nt.links.new(combine_sub.outputs[0], bsdf.inputs["Subsurface Color"])
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.0
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 2.0
    if "Coat Roughness" in bsdf.inputs:
        bsdf.inputs["Coat Roughness"].default_value = 0.0
    bsdf.inputs["IOR"].default_value = 1.3
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = 0.0

    # Translucent BSDF
    translucent = nt.nodes.new("ShaderNodeBsdfTranslucent")
    translucent.inputs["Color"].default_value = main_color

    # MixShader(0.4, principled, translucent)
    mix_shader_1 = nt.nodes.new("ShaderNodeMixShader")
    mix_shader_1.inputs[0].default_value = 0.4
    nt.links.new(bsdf.outputs[0], mix_shader_1.inputs[1])
    nt.links.new(translucent.outputs[0], mix_shader_1.inputs[2])

    # Diffuse BSDF
    diffuse_bsdf = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diffuse_bsdf.inputs["Color"].default_value = main_color
    diffuse_bsdf.inputs["Roughness"].default_value = diffuse_roughness

    # MixShader(mul_1, mix_shader_1, diffuse)
    mix_shader_2 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mul_1.outputs[0], mix_shader_2.inputs[0])
    nt.links.new(mix_shader_1.outputs[0], mix_shader_2.inputs[1])
    nt.links.new(diffuse_bsdf.outputs[0], mix_shader_2.inputs[2])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mix_shader_2.outputs[0], out.inputs["Surface"])
    return mat

def make_whitish_green_succulent(name="WhitishGreenSucculent"):
    noise_scale = float(uniform(5.0, 8.0))

    # ColorRamp element[0] position varies
    cr_elem0_pos = float(uniform(0.0, 0.3))

    mul_factor = float(uniform(1.0, 4.0))

    split_l = float(uniform(0.88, 0.98))
    less_than_threshold = split_l - 0.05

    main_color = _hsv2rgba((float(uniform(0.23, 0.25)), float(uniform(0.40, 0.60)), float(uniform(0.18, 0.25))))
    ramp_low_color = _hsv2rgba((float(uniform(0.20, 0.38)), float(uniform(0.12, 0.25)), float(uniform(0.50, 0.70))))
    diffuse_color = _hsv2rgba((float(uniform(0.23, 0.25)), float(uniform(0.40, 0.60)), float(uniform(0.10, 0.15))))

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    # Build the perturbation chain manually since whitish_green has different CR positions
    noise = _make_noise_musgrave_substitute(nt, noise_scale)

    color_ramp_3 = nt.nodes.new("ShaderNodeValToRGB")
    color_ramp_3.color_ramp.elements[0].position = cr_elem0_pos
    color_ramp_3.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    color_ramp_3.color_ramp.elements[1].position = 0.5273
    color_ramp_3.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    nt.links.new(_noise_fac_output(noise), color_ramp_3.inputs[0])

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])

    sep_xyz = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(mapping.outputs["Vector"], sep_xyz.inputs["Vector"])

    less_than = nt.nodes.new("ShaderNodeMath")
    less_than.operation = "LESS_THAN"
    less_than.inputs[1].default_value = less_than_threshold
    nt.links.new(sep_xyz.outputs["Z"], less_than.inputs[0])

    mul_0 = nt.nodes.new("ShaderNodeMath")
    mul_0.operation = "MULTIPLY"
    nt.links.new(color_ramp_3.outputs["Color"], mul_0.inputs[0])
    nt.links.new(less_than.outputs[0], mul_0.inputs[1])

    mul_1 = nt.nodes.new("ShaderNodeMath")
    mul_1.operation = "MULTIPLY"
    nt.links.new(mul_0.outputs[0], mul_1.inputs[0])
    mul_1.inputs[1].default_value = mul_factor

    # Z-based color ramp: ramp_low_color -> main_color around split_l
    z_ramp = nt.nodes.new("ShaderNodeValToRGB")
    z_ramp.color_ramp.elements[0].position = split_l - float(uniform(0.04, 0.1))
    z_ramp.color_ramp.elements[0].color = ramp_low_color
    z_ramp.color_ramp.elements[1].position = split_l
    z_ramp.color_ramp.elements[1].color = main_color
    nt.links.new(sep_xyz.outputs["Z"], z_ramp.inputs[0])

    # Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(z_ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Subsurface Weight"].default_value = 0.01
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 1.0, 1.0)
    if "Subsurface Color" in bsdf.inputs:
        nt.links.new(z_ramp.outputs["Color"], bsdf.inputs["Subsurface Color"])
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.0
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 2.0
    if "Coat Roughness" in bsdf.inputs:
        bsdf.inputs["Coat Roughness"].default_value = 0.0
    bsdf.inputs["IOR"].default_value = 1.3
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = 0.0

    # Translucent BSDF
    translucent = nt.nodes.new("ShaderNodeBsdfTranslucent")
    translucent.inputs["Color"].default_value = main_color

    # MixShader(0.7, principled, translucent)
    mix_shader_1 = nt.nodes.new("ShaderNodeMixShader")
    mix_shader_1.inputs[0].default_value = 0.7
    nt.links.new(bsdf.outputs[0], mix_shader_1.inputs[1])
    nt.links.new(translucent.outputs[0], mix_shader_1.inputs[2])

    # Diffuse BSDF
    diffuse_bsdf = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diffuse_bsdf.inputs["Color"].default_value = diffuse_color
    diffuse_bsdf.inputs["Roughness"].default_value = 0.5

    # MixShader(mul_1, mix_shader_1, diffuse)
    mix_shader_2 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mul_1.outputs[0], mix_shader_2.inputs[0])
    nt.links.new(mix_shader_1.outputs[0], mix_shader_2.inputs[1])
    nt.links.new(diffuse_bsdf.outputs[0], mix_shader_2.inputs[2])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mix_shader_2.outputs[0], out.inputs["Surface"])
    return mat

# ══════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════
seed_all(SEED)

MODE = np.random.choice(['thin_petal', 'thick_petal'], p=[0.65, 0.35])

# Material is selected inside get_params (same random path as create_asset).
# We don't sample material in Phase 1 because in the material_bit is consumed
# inside get_params() which runs under create_asset's seed. However, since the
# we simply let get_params consume both geometry and material random state together.

# No wear_tear for succulents (plant material — no scratches/edge wear).

# ══════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════

def assign_curve(fc_node, points):
    """Set control points on a ShaderNodeFloatCurve node."""

    curve = fc_node.mapping.curves[0]
    for i, (x, y) in enumerate(points):
        if i < len(curve.points):
            curve.points[i].location = (x, y)
        else:
            curve.points.new(x, y)
    fc_node.mapping.update()

def build_petal_cross_contour_ng():
    ng = bpy.data.node_groups.new('petal_cross_contour', 'GeometryNodeTree')
    s_yb = ng.interface.new_socket('Y_bottom', in_out='INPUT', socket_type='NodeSocketFloat')
    s_x = ng.interface.new_socket('X', in_out='INPUT', socket_type='NodeSocketFloat')
    s_yt = ng.interface.new_socket('Y_top', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput')

    cc = ng.nodes.new('GeometryNodeCurvePrimitiveCircle')
    cc.inputs[0].default_value = 128
    cc.inputs[4].default_value = 0.05

    norm_b = ng.nodes.new('GeometryNodeInputNormal')
    cxyz_b = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(gi.outputs[1], cxyz_b.inputs[0])
    ng.links.new(gi.outputs[0], cxyz_b.inputs[1])

    vmul_b = ng.nodes.new('ShaderNodeVectorMath')
    vmul_b.operation = 'MULTIPLY'
    ng.links.new(norm_b.outputs[0], vmul_b.inputs[0])
    ng.links.new(cxyz_b.outputs[0], vmul_b.inputs[1])

    idx_b = ng.nodes.new('GeometryNodeInputIndex')
    lt = ng.nodes.new('ShaderNodeMath')
    lt.operation = 'LESS_THAN'
    lt.inputs[1].default_value = 64.0
    ng.links.new(idx_b.outputs[0], lt.inputs[0])

    sp_b = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(cc.outputs[0], sp_b.inputs[0])
    ng.links.new(lt.outputs[0], sp_b.inputs[1])
    ng.links.new(vmul_b.outputs[0], sp_b.inputs[3])

    norm_t = ng.nodes.new('GeometryNodeInputNormal')
    cxyz_t = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(gi.outputs[1], cxyz_t.inputs[0])
    ng.links.new(gi.outputs[2], cxyz_t.inputs[1])

    vmul_t = ng.nodes.new('ShaderNodeVectorMath')
    vmul_t.operation = 'MULTIPLY'
    ng.links.new(norm_t.outputs[0], vmul_t.inputs[0])
    ng.links.new(cxyz_t.outputs[0], vmul_t.inputs[1])

    idx_t = ng.nodes.new('GeometryNodeInputIndex')
    gt = ng.nodes.new('ShaderNodeMath')
    gt.operation = 'GREATER_THAN'
    gt.inputs[1].default_value = 63.0
    ng.links.new(idx_t.outputs[0], gt.inputs[0])

    sp_t = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(sp_b.outputs[0], sp_t.inputs[0])
    ng.links.new(gt.outputs[0], sp_t.inputs[1])
    ng.links.new(vmul_t.outputs[0], sp_t.inputs[3])

    noise = ng.nodes.new('ShaderNodeTexNoise')
    noise.noise_dimensions = '4D'
    noise.inputs[1].default_value = 7.0
    noise.inputs[3].default_value = 15.0

    vscale = ng.nodes.new('ShaderNodeVectorMath')
    vscale.operation = 'SCALE'
    vscale.inputs[3].default_value = uniform(0.00, 0.02)
    ng.links.new(noise.outputs[0], vscale.inputs[0])

    sp_n = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(sp_t.outputs[0], sp_n.inputs[0])
    ng.links.new(vscale.outputs[0], sp_n.inputs[3])

    ng.links.new(sp_n.outputs[0], go.inputs[0])
    return ng

def build_petal_geometry_ng(curve_param):
    ng = bpy.data.node_groups.new('petal_geometry', 'GeometryNodeTree')
    ng.interface.new_socket('Y_bottom', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('X', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Y_top', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('petal_stem', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('petal_z', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Mesh', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput')

    cl = ng.nodes.new('GeometryNodeCurvePrimitiveLine')
    cl.inputs[1].default_value = (0.0, 0.0, 0.2)

    rc = ng.nodes.new('GeometryNodeResampleCurve')
    ng.links.new(cl.outputs[0], rc.inputs[0])
    rc.inputs[3].default_value = 64

    pos_s = ng.nodes.new('GeometryNodeInputPosition')
    sp_s = ng.nodes.new('GeometryNodeSplineParameter')

    k = uniform(0.0, 0.3)
    fc_stem = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(sp_s.outputs[0], fc_stem.inputs[1])
    assign_curve(fc_stem, [
        (0.0, 0.0),
        (0.2, 0.2 - k / 2.5),
        (0.4, 0.4 - k / 1.1),
        (0.6, 0.6 - k),
        (0.8, 0.8 - k / 1.5),
        (1.0, 1.0 - k / 3.0),
    ])

    mul_stem = ng.nodes.new('ShaderNodeMath')
    mul_stem.operation = 'MULTIPLY'
    ng.links.new(fc_stem.outputs[0], mul_stem.inputs[0])
    ng.links.new(gi.outputs[3], mul_stem.inputs[1])

    vr_s = ng.nodes.new('ShaderNodeVectorRotate')
    vr_s.rotation_type = 'X_AXIS'
    vr_s.inputs[1].default_value = (0.0, 0.0, 0.2)
    ng.links.new(pos_s.outputs[0], vr_s.inputs[0])
    ng.links.new(mul_stem.outputs[0], vr_s.inputs[3])

    sp_curv = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(rc.outputs[0], sp_curv.inputs[0])
    ng.links.new(vr_s.outputs[0], sp_curv.inputs[3])

    sp_z = ng.nodes.new('GeometryNodeSplineParameter')
    fc_z = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(sp_z.outputs[0], fc_z.inputs[1])
    assign_curve(fc_z, [
        (0.0, curve_param[0]),
        (0.2, curve_param[1] * (1.0 + normal(0, 0.04))),
        (0.4, curve_param[2] * (1.0 + normal(0, 0.1))),
        (0.6, curve_param[3] * (1.0 + normal(0, 0.03))),
        (0.8, curve_param[4] * (1.0 + normal(0, 0.06))),
        (0.9, curve_param[5] * (1.0 + normal(0, 0.04))),
        (1.0, 0.0),
    ])

    mul_z = ng.nodes.new('ShaderNodeMath')
    mul_z.operation = 'MULTIPLY'
    ng.links.new(fc_z.outputs[0], mul_z.inputs[0])
    ng.links.new(gi.outputs[4], mul_z.inputs[1])

    scr = ng.nodes.new('GeometryNodeSetCurveRadius')
    ng.links.new(sp_curv.outputs[0], scr.inputs[0])
    ng.links.new(mul_z.outputs[0], scr.inputs[2])

    cc_ng = build_petal_cross_contour_ng()
    cc_grp = ng.nodes.new('GeometryNodeGroup')
    cc_grp.node_tree = cc_ng
    ng.links.new(gi.outputs[0], cc_grp.inputs[0])
    ng.links.new(gi.outputs[1], cc_grp.inputs[1])
    ng.links.new(gi.outputs[2], cc_grp.inputs[2])

    c2m = ng.nodes.new('GeometryNodeCurveToMesh')
    ng.links.new(scr.outputs[0], c2m.inputs[0])
    ng.links.new(cc_grp.outputs[0], c2m.inputs[1])
    ng.links.new(mul_z.outputs[0], c2m.inputs[2])
    c2m.inputs[3].default_value = True

    ng.links.new(c2m.outputs[0], go.inputs[0])
    return ng

def build_petal_on_base_ng(R):
    ng = bpy.data.node_groups.new('petal_on_base', 'GeometryNodeTree')
    ng.interface.new_socket('Radius', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('x_R', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('z_R', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Resolution', in_out='INPUT', socket_type='NodeSocketInt')
    ng.interface.new_socket('Instance', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Scale', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('base_z', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Instances', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput')

    cc = ng.nodes.new('GeometryNodeCurvePrimitiveCircle')
    ng.links.new(gi.outputs[3], cc.inputs[0])
    ng.links.new(gi.outputs[0], cc.inputs[4])

    rv_x = ng.nodes.new('FunctionNodeRandomValue')
    rv_x.data_type = 'FLOAT'
    rv_x.inputs[2].default_value = -0.8 * R
    rv_x.inputs[3].default_value = 0.8 * R

    rv_y = ng.nodes.new('FunctionNodeRandomValue')
    rv_y.data_type = 'FLOAT'
    rv_y.inputs[2].default_value = -0.8 * R
    rv_y.inputs[3].default_value = 0.8 * R

    rv_z = ng.nodes.new('FunctionNodeRandomValue')
    rv_z.data_type = 'FLOAT'
    rv_z.inputs[2].default_value = -0.2 * R
    rv_z.inputs[3].default_value = 0.2 * R

    add_z = ng.nodes.new('ShaderNodeMath')
    add_z.operation = 'ADD'
    ng.links.new(rv_z.outputs[1], add_z.inputs[0])
    ng.links.new(gi.outputs[6], add_z.inputs[1])

    cxyz_p = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(rv_x.outputs[1], cxyz_p.inputs[0])
    ng.links.new(rv_y.outputs[1], cxyz_p.inputs[1])
    ng.links.new(add_z.outputs[0], cxyz_p.inputs[2])

    sp_p = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(cc.outputs[0], sp_p.inputs[0])
    ng.links.new(cxyz_p.outputs[0], sp_p.inputs[3])

    norm_a = ng.nodes.new('GeometryNodeInputNormal')
    align = ng.nodes.new('FunctionNodeAlignEulerToVector')
    align.pivot_axis = 'Z'
    ng.links.new(norm_a.outputs[0], align.inputs[2])

    rv_s = ng.nodes.new('FunctionNodeRandomValue')
    rv_s.data_type = 'FLOAT'
    rv_s.inputs[2].default_value = 0.7
    rv_s.inputs[3].default_value = 1.2

    iop = ng.nodes.new('GeometryNodeInstanceOnPoints')
    ng.links.new(sp_p.outputs[0], iop.inputs[0])
    ng.links.new(gi.outputs[4], iop.inputs[2])
    ng.links.new(align.outputs[0], iop.inputs[5])
    ng.links.new(rv_s.outputs[1], iop.inputs[6])

    real = ng.nodes.new('GeometryNodeRealizeInstances')
    ng.links.new(iop.outputs[0], real.inputs[0])

    rv_xr = ng.nodes.new('FunctionNodeRandomValue')
    rv_xr.data_type = 'FLOAT'
    rv_xr.inputs[2].default_value = -0.1
    rv_xr.inputs[3].default_value = 0.1
    add_xr = ng.nodes.new('ShaderNodeMath')
    add_xr.operation = 'ADD'
    ng.links.new(rv_xr.outputs[1], add_xr.inputs[0])
    ng.links.new(gi.outputs[1], add_xr.inputs[1])

    rv_zr = ng.nodes.new('FunctionNodeRandomValue')
    rv_zr.data_type = 'FLOAT'
    rv_zr.inputs[2].default_value = -0.3
    rv_zr.inputs[3].default_value = 0.3
    add_zr = ng.nodes.new('ShaderNodeMath')
    add_zr.operation = 'ADD'
    ng.links.new(rv_zr.outputs[1], add_zr.inputs[0])
    ng.links.new(gi.outputs[2], add_zr.inputs[1])

    cxyz_r = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(add_xr.outputs[0], cxyz_r.inputs[0])
    ng.links.new(add_zr.outputs[0], cxyz_r.inputs[2])

    ri = ng.nodes.new('GeometryNodeRotateInstances')
    ng.links.new(real.outputs[0], ri.inputs[0])
    ng.links.new(cxyz_r.outputs[0], ri.inputs[2])

    si = ng.nodes.new('GeometryNodeScaleInstances')
    ng.links.new(ri.outputs[0], si.inputs[0])
    ng.links.new(gi.outputs[5], si.inputs[2])

    ng.links.new(si.outputs[0], go.inputs[0])
    return ng

def get_params(mode):
    """Get geometry + material params. Returns (params_dict, material_maker_func)."""

    if mode == 'thin_petal':
        params = {}
        params['cross_y_bottom'] = uniform(0.08, 0.25)
        params['cross_y_top'] = uniform(-0.04, 0.02)
        params['cross_x'] = uniform(0.3, 0.6)
        num_bases = randint(5, 8)
        params['num_bases'] = num_bases
        base_radius, petal_x_R, base_petal_num, base_petal_scale, base_z = [], [], [], [], []
        init_base_radius, diff_base_radius = uniform(0.09, 0.11), 0.1
        init_x_R, diff_x_R = uniform(-1.2, -1.35), uniform(-0.7, -1.1)
        init_petal_num = randint(num_bases, 15)
        diff_petal_scale = uniform(0.5, 0.9)
        for i in range(num_bases):
            base_radius.append(init_base_radius - (i * diff_base_radius) / num_bases)
            petal_x_R.append(init_x_R - (i * diff_x_R) / num_bases)
            base_petal_num.append(init_petal_num - i + randint(0, 2))
            base_petal_scale.append(1.0 - (i * diff_petal_scale) / num_bases)
            base_z.append(0.0 + i * uniform(0.005, 0.008))
        params['base_radius'] = base_radius
        params['petal_x_R'] = petal_x_R
        params['base_petal_num'] = base_petal_num
        params['base_petal_scale'] = base_petal_scale
        params['base_z'] = base_z
        contour_bit = randint(0, 3)
        material_bit = randint(0, 3)
        if contour_bit == 0:
            params['petal_curve_param'] = [0.08, 0.4, 0.46, 0.36, 0.17, 0.05]
        elif contour_bit == 1:
            params['petal_curve_param'] = [0.22, 0.37, 0.50, 0.49, 0.30, 0.08]
        else:
            params['petal_curve_param'] = [0.21, 0.26, 0.31, 0.36, 0.29, 0.16]

        if material_bit == 0:
            mat_func = make_green_transition_succulent
        elif material_bit == 1:
            mat_func = make_pink_transition_succulent
        else:
            mat_func = make_green_succulent
        return params, mat_func

    elif mode == 'thick_petal':
        params = {}
        params['cross_y_bottom'] = uniform(0.22, 0.30)
        params['cross_y_top'] = uniform(0.08, 0.15)
        params['cross_x'] = uniform(0.14, 0.16)
        num_bases = randint(3, 6)
        params['num_bases'] = num_bases
        base_radius, petal_x_R, base_petal_num, base_petal_scale, base_z = [], [], [], [], []
        init_base_radius, diff_base_radius = uniform(0.12, 0.14), 0.11
        init_x_R, diff_x_R = uniform(-1.3, -1.4), uniform(-0.1, -1.2)
        init_petal_num = randint(num_bases, 12)
        diff_petal_scale = uniform(0.6, 0.9)
        for i in range(num_bases):
            base_radius.append(init_base_radius - (i * diff_base_radius) / num_bases)
            petal_x_R.append(init_x_R - (i * diff_x_R) / num_bases)
            base_petal_num.append(init_petal_num - i + randint(0, 2))
            base_petal_scale.append(1.0 - (i * diff_petal_scale) / num_bases)
            base_z.append(0.0 + i * uniform(0.005, 0.006))
        params['base_radius'] = base_radius
        params['petal_x_R'] = petal_x_R
        params['base_petal_num'] = base_petal_num
        params['base_petal_scale'] = base_petal_scale
        params['base_z'] = base_z
        contour_bit = randint(0, 2)
        material_bit = randint(0, 2)
        if contour_bit == 0:
            params['petal_curve_param'] = [0.10, 0.36, 0.44, 0.45, 0.30, 0.24]
        else:
            params['petal_curve_param'] = [0.16, 0.35, 0.48, 0.42, 0.30, 0.18]

        if material_bit == 0:
            mat_func = make_yellow_succulent
        else:
            mat_func = make_whitish_green_succulent
        return params, mat_func
    else:
        raise NotImplementedError(f"Unknown mode: {mode}")

def build_succulent_ng(params):
    ng = bpy.data.node_groups.new('SucculentGeometry', 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput')

    v_yb = ng.nodes.new('ShaderNodeValue')
    v_yb.outputs[0].default_value = params['cross_y_bottom']
    v_x = ng.nodes.new('ShaderNodeValue')
    v_x.outputs[0].default_value = params['cross_x']
    v_yt = ng.nodes.new('ShaderNodeValue')
    v_yt.outputs[0].default_value = params['cross_y_top']
    v_stem = ng.nodes.new('ShaderNodeValue')
    v_stem.outputs[0].default_value = np.abs(normal(0, 1.0))
    v_z = ng.nodes.new('ShaderNodeValue')
    v_z.outputs[0].default_value = uniform(0.4, 0.9)

    base_outputs = []

    for i in range(params['num_bases']):
        pg_ng = build_petal_geometry_ng(params['petal_curve_param'])
        pg_grp = ng.nodes.new('GeometryNodeGroup')
        pg_grp.node_tree = pg_ng
        ng.links.new(v_yb.outputs[0], pg_grp.inputs[0])
        ng.links.new(v_x.outputs[0], pg_grp.inputs[1])
        ng.links.new(v_yt.outputs[0], pg_grp.inputs[2])
        ng.links.new(v_stem.outputs[0], pg_grp.inputs[3])
        ng.links.new(v_z.outputs[0], pg_grp.inputs[4])

        pob_ng = build_petal_on_base_ng(params['base_radius'][i])
        pob_grp = ng.nodes.new('GeometryNodeGroup')
        pob_grp.node_tree = pob_ng

        v_br = ng.nodes.new('ShaderNodeValue')
        v_br.outputs[0].default_value = params['base_radius'][i]
        v_xr = ng.nodes.new('ShaderNodeValue')
        v_xr.outputs[0].default_value = params['petal_x_R'][i]
        v_zr = ng.nodes.new('ShaderNodeValue')
        v_zr.outputs[0].default_value = -1.57 + normal(0, 0.3)
        v_pn = ng.nodes.new('FunctionNodeInputInt')
        v_pn.integer = params['base_petal_num'][i]
        v_ps = ng.nodes.new('ShaderNodeValue')
        v_ps.outputs[0].default_value = params['base_petal_scale'][i]
        v_bz = ng.nodes.new('ShaderNodeValue')
        v_bz.outputs[0].default_value = params['base_z'][i]

        ng.links.new(v_br.outputs[0], pob_grp.inputs[0])
        ng.links.new(v_xr.outputs[0], pob_grp.inputs[1])
        ng.links.new(v_zr.outputs[0], pob_grp.inputs[2])
        ng.links.new(v_pn.outputs[0], pob_grp.inputs[3])
        ng.links.new(pg_grp.outputs[0], pob_grp.inputs[4])
        ng.links.new(v_ps.outputs[0], pob_grp.inputs[5])
        ng.links.new(v_bz.outputs[0], pob_grp.inputs[6])

        base_outputs.append(pob_grp)

    join = ng.nodes.new('GeometryNodeJoinGeometry')
    for bo in base_outputs:
        ng.links.new(bo.outputs[0], join.inputs[0])

    smooth = ng.nodes.new('GeometryNodeSetShadeSmooth')
    ng.links.new(join.outputs[0], smooth.inputs[0])

    real = ng.nodes.new('GeometryNodeRealizeInstances')
    ng.links.new(smooth.outputs[0], real.inputs[0])

    ng.links.new(real.outputs[0], go.inputs[0])
    return ng

# ══════════════════════════════════════════════════════════════════════════
# Build: geometry + material assignment
# ══════════════════════════════════════════════════════════════════════════

def build(seed=SEED):
    np.random.seed(seed)

    # Mode was already selected in Phase 1 (raw seed)
    # Consume the mode choice again to maintain random state alignment
    _ = np.random.choice(['thin_petal', 'thick_petal'], p=[0.65, 0.35])

    params, mat_func = get_params(MODE)

    # Create the material (consumes numpy.random state for shader params)
    succulent_mat = mat_func(name="SucculentMaterial")

    bpy.ops.mesh.primitive_plane_add(
        size=1, enter_editmode=False, align='WORLD',
        location=(0, 0, 0), scale=(1, 1, 1),
    )
    obj = bpy.context.active_object

    tree = build_succulent_ng(params)

    mod = obj.modifiers.new('Succulent', 'NODES')
    mod.node_group = tree

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

    obj.scale = (0.2, 0.2, 0.2)
    obj.location.z += 0.01
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Assign material to the succulent mesh
    obj.data.materials.append(succulent_mat)
    for i in range(len(obj.data.materials)):
        if obj.data.materials[i] is None:
            obj.data.materials[i] = succulent_mat

    return obj

build(SEED)

