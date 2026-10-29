# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_for_constructing_a_model_of_a_tubular_porous_bioinspired_structur" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code for constructing a model of a tubular porous bioinspired structure with noise. Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
num_tubes = 22  # Number of tubes
noise_value = 0.06  # Noise value for positioning

def setup_tubule_structure(tube_quantity, noise_variation):
    # Setup a cube and subtract a grid of noisy tubes
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tube_quantity))
    spacing = 2 / grid_size
    start_pos = -1 + spacing / 2

    positions = [(start_pos + (i % grid_size) * spacing, 
                  start_pos + (i // grid_size) * spacing)
                 for i in range(tube_quantity)]

    noisy_positions = [(x + random.uniform(-noise_variation, noise_variation), 
                        y + random.uniform(-noise_variation, noise_variation)) for x, y in positions]

    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object

        bool_mod = cube.modifiers.new(name="Tube_{:.2f}_{:.2f}".format(x, y), type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tube

        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        bpy.data.objects.remove(tube, do_unlink=True)

# Execute the setup for the tubular structure
setup_tubule_structure(num_tubes, noise_value)
