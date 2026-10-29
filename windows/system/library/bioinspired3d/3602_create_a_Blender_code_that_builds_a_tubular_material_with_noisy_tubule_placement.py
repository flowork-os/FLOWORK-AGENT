# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_Blender_code_that_builds_a_tubular_material_with_noisy_tubule_placement" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a Blender code that builds a tubular material with noisy tubule placement.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule arrangement settings
num_tubules = 12  # Count of tubules
noise_variance = 0.06  # Noise deviation

def create_tubule_grid(tubule_count, noise_amount):
    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    initial_offset = -1 + spacing / 2

    # Calculate positions for tubules
    positions = [(initial_offset + (i % grid_size) * spacing,
                  initial_offset + (i // grid_size) * spacing)
                 for i in range(tubule_count)]

    # Add noise to positions
    noisy_positions = [(x + random.uniform(-noise_amount, noise_amount),
                        y + random.uniform(-noise_amount, noise_amount)) for x, y in positions]

    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        bool_modifier = cube_object.modifiers.new(name="BooleanOperation", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the grid of tubules
create_tubule_grid(num_tubules, noise_variance)
