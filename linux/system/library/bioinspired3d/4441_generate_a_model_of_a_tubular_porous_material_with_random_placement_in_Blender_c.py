# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_a_tubular_porous_material_with_random_placement_in_Blender_c" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of a tubular porous material with random placement in Blender code think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the number of tubules and noise
num_tubules = 12
noise_amount = 0.06

def build_tubular_structure(tubule_count, noise):
    # Initialize a cube and create tubules with noise
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_obj = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    # Calculate positions for tubules
    positions = [(offset + (i % grid_size) * spacing,
                  offset + (i // grid_size) * spacing)
                 for i in range(tubule_count)]

    # Apply noise to positions
    noisy_positions = [(x + random.uniform(-noise, noise),
                        y + random.uniform(-noise, noise)) for x, y in positions]

    # Create tubules and apply Boolean modifiers
    for pos_x, pos_y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        tubule = bpy.context.object
        bool_modifier = cube_obj.modifiers.new(name=f"Cut_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        bpy.context.view_layer.objects.active = cube_obj
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the construction of the structure
build_tubular_structure(num_tubules, noise_amount)
