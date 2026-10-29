# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_for_constructing_a_tubular_porous_material_with_noise_Think_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code for constructing a tubular porous material with noise Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the cylindrical structures
num_tubules = 15  # Total count of tubules
max_noise = 0.07  # Noise factor for positioning

def generate_tubules(total_tubules=15, noise_factor=0.07):
    # Create a base cube and arrange tubules within it
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_dimension
    initial_offset = -1 + spacing / 2

    # Calculate positions for the tubules
    positions = [(initial_offset + (i % grid_dimension) * spacing, 
                  initial_offset + (i // grid_dimension) * spacing) 
                 for i in range(total_tubules)]

    # Apply noise to positions
    noisy_positions = [(x + random.uniform(-noise_factor, noise_factor), 
                        y + random.uniform(-noise_factor, noise_factor)) for x, y in positions]

    # Subtract tubules from the cube
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule_cylinder = bpy.context.object

        # Create and apply Boolean modifier
        bool_modifier = base_cube.modifiers.new(name='Boolean', type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule_cylinder

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        bpy.data.objects.remove(tubule_cylinder, do_unlink=True)

# Create the tubular structure
generate_tubules(num_tubules, max_noise)
