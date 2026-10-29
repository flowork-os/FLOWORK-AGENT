# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_tubular_material_with_random_placement_in_python_blender_code_Think" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a tubular material with random placement in python blender code Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_of_tubules = 18  # Total number of tubules
position_noise = 0.08  # Noise for position adjustment

def create_cube():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    return bpy.context.object

def generate_tubule_positions(count):
    grid_dim = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2
    return [(offset + (i % grid_dim) * spacing,
             offset + (i // grid_dim) * spacing)
            for i in range(count)]

def apply_noise_to_positions(positions, noise):
    return [(x + random.uniform(-noise, noise),
             y + random.uniform(-noise, noise)) for x, y in positions]

def perform_subtraction(cube, positions):
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        bool_mod = cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

base_cube = create_cube()
positions = generate_tubule_positions(num_of_tubules)
noisy_positions = apply_noise_to_positions(positions, position_noise)
perform_subtraction(base_cube, noisy_positions)
