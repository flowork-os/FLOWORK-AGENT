# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_tubular_material_with_noise_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a tubular material with noise using code in Blender

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Variables for the tubular structure
num_tubules = 20  # Total number of tubules
noise_level = 0.05  # Noise deviation for tubule positions

def create_structure(num_tubules=20, noise=0.05):
    # Create a cube and subtract tubules with noise
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    # Calculate positions for tubules
    positions = [(offset + (i % grid_size) * spacing,
                  offset + (i // grid_size) * spacing)
                 for i in range(num_tubules)]

    # Add noise to positions
    noisy_positions = [(x + random.uniform(-noise, noise),
                        y + random.uniform(-noise, noise)) for x, y in positions]

    # Subtract tubules from the cube
    for pos_x, pos_y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        tubule = bpy.context.object

        # Create and apply Boolean modifier
        bool_mod = base_cube.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        # Cleanup: remove the tubule
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the creation of the structure
create_structure(num_tubules, noise_level)
