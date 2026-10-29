# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_Python_script_that_builds_a_cube_of_tubular_bioinspired_materia" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender Python script that builds a cube of tubular bioinspired material with random placement. Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule specifications
num_tubules = 12
noise_amount = 0.04

def create_structure(num_tubules, noise_amount):
    # Create the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    start = -1 + spacing / 2

    # Calculate positions and add noise
    positions = [(start + (i % grid_size) * spacing, start + (i // grid_size) * spacing) for i in range(num_tubules)]
    noisy_positions = [(x + random.uniform(-noise_amount, noise_amount), y + random.uniform(-noise_amount, noise_amount)) for x, y in positions]

    # Subtract tubules from the cube
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        boolean_modifier = cube.modifiers.new(name="Bool_{:.2f}_{:.2f}".format(x, y), type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

create_structure(num_tubules, noise_amount)
