# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_code_build_a_model_of_a_tubular_bioinspired_material_with_noi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender code build a model of a tubular bioinspired material with noise think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

tube_total = 20  # Total number of tubes
noise_variation = 0.06  # Noise applied to tube positions

def setup_cube():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    return bpy.context.object

def calculate_positions(count):
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    start = -1 + spacing / 2
    return [(start + (i % grid_size) * spacing,
             start + (i // grid_size) * spacing)
            for i in range(count)]

def add_noise(positions, noise):
    return [(x + random.uniform(-noise, noise),
             y + random.uniform(-noise, noise)) for x, y in positions]

def subtract_tubes(cube, positions):
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object
        
        bool_modifier = cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tube
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tube, do_unlink=True)

base = setup_cube()
positions = calculate_positions(tube_total)
noisy_positions = add_noise(positions, noise_variation)
subtract_tubes(base, noisy_positions)
