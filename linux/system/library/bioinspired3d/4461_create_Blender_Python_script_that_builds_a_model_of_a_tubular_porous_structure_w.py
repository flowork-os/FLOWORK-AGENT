# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_Blender_Python_script_that_builds_a_model_of_a_tubular_porous_structure_w" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create Blender Python script that builds a model of a tubular porous structure with random placement. Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set up parameters for the tubular structure
count_tubules = 12
noise_amount = 0.1

def make_tubules(count, noise):
    # This function generates a grid of tubules with added noise
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    start_pos = -1 + spacing / 2
    positions = [(start_pos + (i % grid_size) * spacing, 
                  start_pos + (i // grid_size) * spacing) 
                 for i in range(count)]
    noisy_positions = [(x + random.uniform(-noise, noise), 
                        y + random.uniform(-noise, noise)) for x, y in positions]
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        bool_modifier = cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Generate the tubules
make_tubules(count_tubules, noise_amount)
