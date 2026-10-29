# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_Blender_script_that_generates_a_tubular_material_with_noisy_tubule_plac" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a Blender script that generates a tubular material with noisy tubule placement.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular structure
tubule_quantity = 18
jitter_strength = 0.08

def tubule_grid(tubule_quantity, jitter_strength):
    # Function to create a grid of tubules with noise
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_quantity))
    spacing = 2 / grid_size
    start_position = -1 + spacing / 2

    # Calculate positions
    positions = [(start_position + (i % grid_size) * spacing,
                  start_position + (i // grid_size) * spacing)
                 for i in range(tubule_quantity)]

    # Add noise to the positions
    noisy_positions = [(x + random.uniform(-jitter_strength, jitter_strength),
                        y + random.uniform(-jitter_strength, jitter_strength)) for x, y in positions]

    # Subtract tubules from the cube
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        boolean_modifier = base_cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular grid
tubule_grid(tubule_quantity, jitter_strength)
