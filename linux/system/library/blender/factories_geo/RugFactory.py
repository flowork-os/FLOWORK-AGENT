# [FL_INDEX: keywords="blender_factory, procedural_3d, RugFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: RugFactory | Category: factories_geo
# Prompt: A flat oval rug rendered as a 3D model with a clean, minimalist appearance.

import os
import random

import bpy
import numpy as np

SEED = int(os.environ.get("SEED", "0"))
np.random.seed(SEED)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    bpy.context.scene.cursor.location = (0, 0, 0)

def apply_tf(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def add_mod(obj, mtype, **kw):
    m = obj.modifiers.new("", mtype)
    for k, v in kw.items():
        setattr(m, k, v)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=m.name)
    return obj

def clip_gaussian(mean, std, lo, hi):
    return float(np.clip(np.random.normal(mean, std), lo, hi))

def random_color(palette):
    """Pick a random color from a palette category."""

    palettes = {
        'warm': [
            (0.55, 0.12, 0.08, 1.0),  # deep red
            (0.72, 0.25, 0.10, 1.0),  # rust
            (0.80, 0.55, 0.15, 1.0),  # gold
            (0.45, 0.10, 0.05, 1.0),  # burgundy
            (0.60, 0.30, 0.12, 1.0),  # terracotta
            (0.35, 0.08, 0.12, 1.0),  # wine
        ],
        'cool': [
            (0.10, 0.15, 0.45, 1.0),  # navy
            (0.20, 0.35, 0.55, 1.0),  # slate blue
            (0.55, 0.60, 0.65, 1.0),  # silver gray
            (0.85, 0.85, 0.80, 1.0),  # off-white
            (0.15, 0.30, 0.35, 1.0),  # teal
            (0.08, 0.20, 0.40, 1.0),  # deep blue
        ],
        'neutral': [
            (0.75, 0.65, 0.50, 1.0),  # cream
            (0.55, 0.45, 0.30, 1.0),  # khaki
            (0.40, 0.30, 0.20, 1.0),  # brown
            (0.85, 0.78, 0.65, 1.0),  # beige
            (0.30, 0.22, 0.15, 1.0),  # dark brown
            (0.65, 0.55, 0.40, 1.0),  # sand
        ],
        'vibrant': [
            (0.70, 0.10, 0.15, 1.0),  # bright red
            (0.10, 0.35, 0.20, 1.0),  # forest green
            (0.65, 0.50, 0.05, 1.0),  # mustard
            (0.15, 0.10, 0.50, 1.0),  # royal purple
            (0.85, 0.45, 0.10, 1.0),  # orange
            (0.05, 0.25, 0.45, 1.0),  # cerulean
        ],
    }
    colors = palettes.get(palette, palettes['warm'])
    return colors[np.random.randint(len(colors))]

def add_rug_material(obj):
    """Add a procedural rug material with pattern and color variation."""

    mat = bpy.data.materials.new("rug_material")
    mat.use_nodes = True
    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links

    # Clear default nodes
    for n in list(nodes):
        nodes.remove(n)

    # Pick palette and pattern
    palette = np.random.choice(['warm', 'cool', 'neutral', 'vibrant'])
    pattern_type = np.random.choice(['voronoi', 'stripes', 'checker', 'medallion'])

    color1 = random_color(palette)
    color2 = random_color(palette)
    # Ensure colors are different enough
    while sum(abs(a - b) for a, b in zip(color1[:3], color2[:3])) < 0.3:
        color2 = random_color(palette)
    color3 = random_color(palette)

    # Output node
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (800, 0)

    # Principled BSDF
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (600, 0)
    bsdf.inputs['Roughness'].default_value = np.random.uniform(0.85, 0.98)
    bsdf.inputs['Specular IOR Level'].default_value = np.random.uniform(0.02, 0.08)
    links.new(bsdf.outputs[0], output.inputs[0])

    # Texture coordinates (use Object for position-based texturing)
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-600, 0)

    mapping = nodes.new('ShaderNodeMapping')
    mapping.location = (-400, 0)
    links.new(tex_coord.outputs['Object'], mapping.inputs[0])

    if pattern_type == 'voronoi':
        # Voronoi pattern (like traditional rug motifs)
        voronoi = nodes.new('ShaderNodeTexVoronoi')
        voronoi.location = (-200, 100)
        voronoi.voronoi_dimensions = '2D'
        voronoi.inputs['Scale'].default_value = np.random.uniform(4, 12)
        links.new(mapping.outputs[0], voronoi.inputs['Vector'])

        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.location = (0, 100)
        ramp.color_ramp.elements[0].color = color1
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[1].color = color2
        ramp.color_ramp.elements[1].position = 1.0
        # Add middle color
        mid = ramp.color_ramp.elements.new(np.random.uniform(0.3, 0.7))
        mid.color = color3
        links.new(voronoi.outputs['Distance'], ramp.inputs[0])

        # Mix with noise for subtle variation
        noise = nodes.new('ShaderNodeTexNoise')
        noise.location = (-200, -100)
        noise.inputs['Scale'].default_value = np.random.uniform(15, 40)
        noise.inputs['Detail'].default_value = np.random.uniform(3, 8)
        links.new(mapping.outputs[0], noise.inputs['Vector'])

        mix = nodes.new('ShaderNodeMix')
        mix.location = (200, 0)
        mix.data_type = 'RGBA'
        mix.inputs['Factor'].default_value = np.random.uniform(0.05, 0.15)
        links.new(ramp.outputs[0], mix.inputs[6])  # Color A
        links.new(noise.outputs[0], mix.inputs[7])  # Color B
        links.new(mix.outputs[2], bsdf.inputs['Base Color'])

    elif pattern_type == 'stripes':
        # Stripe pattern
        sep = nodes.new('ShaderNodeSeparateXYZ')
        sep.location = (-200, 0)
        links.new(mapping.outputs[0], sep.inputs[0])

        # Use X or Y for stripe direction
        stripe_axis = np.random.choice([0, 1])
        stripe_scale = np.random.uniform(3, 10)

        math_mul = nodes.new('ShaderNodeMath')
        math_mul.operation = 'MULTIPLY'
        math_mul.location = (0, 0)
        math_mul.inputs[1].default_value = stripe_scale
        links.new(sep.outputs[stripe_axis], math_mul.inputs[0])

        math_sin = nodes.new('ShaderNodeMath')
        math_sin.operation = 'SINE'
        math_sin.location = (150, 0)
        links.new(math_mul.outputs[0], math_sin.inputs[0])

        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.location = (300, 0)
        ramp.color_ramp.interpolation = 'CONSTANT'
        ramp.color_ramp.elements[0].color = color1
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[1].color = color2
        ramp.color_ramp.elements[1].position = 0.5
        mid = ramp.color_ramp.elements.new(0.75)
        mid.color = color3
        links.new(math_sin.outputs[0], ramp.inputs[0])

        links.new(ramp.outputs[0], bsdf.inputs['Base Color'])

    elif pattern_type == 'checker':
        # Checker pattern
        checker = nodes.new('ShaderNodeTexChecker')
        checker.location = (-200, 0)
        checker.inputs['Scale'].default_value = np.random.uniform(4, 12)
        checker.inputs['Color1'].default_value = color1
        checker.inputs['Color2'].default_value = color2
        links.new(mapping.outputs[0], checker.inputs['Vector'])

        links.new(checker.outputs[0], bsdf.inputs['Base Color'])

    else:  # medallion
        # Radial gradient for medallion pattern
        sep = nodes.new('ShaderNodeSeparateXYZ')
        sep.location = (-200, 0)
        links.new(mapping.outputs[0], sep.inputs[0])

        # sqrt(x^2 + y^2) for radial distance
        math_x2 = nodes.new('ShaderNodeMath')
        math_x2.operation = 'MULTIPLY'
        math_x2.location = (0, 100)
        links.new(sep.outputs[0], math_x2.inputs[0])
        links.new(sep.outputs[0], math_x2.inputs[1])

        math_y2 = nodes.new('ShaderNodeMath')
        math_y2.operation = 'MULTIPLY'
        math_y2.location = (0, -100)
        links.new(sep.outputs[1], math_y2.inputs[0])
        links.new(sep.outputs[1], math_y2.inputs[1])

        math_add = nodes.new('ShaderNodeMath')
        math_add.operation = 'ADD'
        math_add.location = (150, 0)
        links.new(math_x2.outputs[0], math_add.inputs[0])
        links.new(math_y2.outputs[0], math_add.inputs[1])

        math_sqrt = nodes.new('ShaderNodeMath')
        math_sqrt.operation = 'SQRT'
        math_sqrt.location = (300, 0)
        links.new(math_add.outputs[0], math_sqrt.inputs[0])

        # Scale and repeat rings
        math_ring = nodes.new('ShaderNodeMath')
        math_ring.operation = 'MULTIPLY'
        math_ring.location = (400, 0)
        math_ring.inputs[1].default_value = np.random.uniform(3, 8)
        links.new(math_sqrt.outputs[0], math_ring.inputs[0])

        math_frac = nodes.new('ShaderNodeMath')
        math_frac.operation = 'FRACT'
        math_frac.location = (500, 0)
        links.new(math_ring.outputs[0], math_frac.inputs[0])

        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.location = (650, 200)
        ramp.color_ramp.elements[0].color = color1
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[1].color = color2
        ramp.color_ramp.elements[1].position = 0.5
        mid = ramp.color_ramp.elements.new(0.8)
        mid.color = color3
        links.new(math_frac.outputs[0], ramp.inputs[0])

        links.new(ramp.outputs[0], bsdf.inputs['Base Color'])

    # Add subtle bump for fabric texture
    bump_noise = nodes.new('ShaderNodeTexNoise')
    bump_noise.location = (200, -200)
    bump_noise.inputs['Scale'].default_value = np.random.uniform(80, 200)
    bump_noise.inputs['Detail'].default_value = np.random.uniform(4, 10)
    bump_noise.inputs['Roughness'].default_value = 0.7
    links.new(mapping.outputs[0], bump_noise.inputs['Vector'])

    bump = nodes.new('ShaderNodeBump')
    bump.location = (400, -200)
    bump.inputs['Strength'].default_value = np.random.uniform(0.1, 0.3)
    links.new(bump_noise.outputs[0], bump.inputs['Height'])
    links.new(bump.outputs[0], bsdf.inputs['Normal'])

    obj.data.materials.append(mat)

def build_rug():
    clear_scene()

    # Parameters
    width = clip_gaussian(3, 1, 2, 6)
    rug_shape = np.random.choice(["rectangle", "circle", "rounded", "ellipse"])
    length = width * np.random.uniform(1.0, 1.5)
    if rug_shape == "circle":
        length = width
    rounded_buffer = width * np.random.uniform(0.1, 0.5)
    thickness = np.random.uniform(0.01, 0.02)

    if rug_shape == "rectangle":
        bpy.ops.mesh.primitive_plane_add(size=2.0)
        rug = bpy.context.active_object
        rug.scale = (length / 2, width / 2, 1)
        apply_tf(rug)
    elif rug_shape == "rounded":
        bpy.ops.mesh.primitive_plane_add(size=2.0)
        rug = bpy.context.active_object
        rug.scale = (length / 2, width / 2, 1)
        apply_tf(rug)
        add_mod(rug, "BEVEL", width=rounded_buffer, segments=16)
    else:
        bpy.ops.mesh.primitive_circle_add(vertices=128, radius=1.0, fill_type="NGON")
        rug = bpy.context.active_object
        rug.scale = (length / 2, width / 2, 1)
        apply_tf(rug)

    rug.name = "RugFactory"

    # Add procedural rug material
    add_rug_material(rug)

    # SOLIDIFY with offset=1 (extrude upward)
    add_mod(rug, "SOLIDIFY", thickness=thickness, offset=1)

    return rug

rug = build_rug()
