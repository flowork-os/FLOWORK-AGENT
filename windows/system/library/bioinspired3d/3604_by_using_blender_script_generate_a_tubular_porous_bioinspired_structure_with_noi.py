# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_blender_script_generate_a_tubular_porous_bioinspired_structure_with_noi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using blender script generate a tubular porous bioinspired structure with noise.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular structure
number_of_tubules = 16  # Total number of tubules in the structure
max_noise = 0.07  # Maximum noise deviation applied to tubule positions

def generate_tubules(count=16, noise=0.07):
    # Function to create a cube with a grid of tubules with noise placement.
    # 1. Initialize a cube.
    # 2. Position tubules in a grid.
    # 3. Introduce noise to positions.
    # 4. Use Boolean modifiers to subtract tubules.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dimension
    initial_offset = -1 + spacing / 2

    # Generate positions for tubules in the grid
    tubule_positions = [(initial_offset + (i % grid_dimension) * spacing,
                         initial_offset + (i // grid_dimension) * spacing)
                        for i in range(count)]

    # Add random noise to each position
    jittered_positions = [(x + random.uniform(-noise, noise),
                           y + random.uniform(-noise, noise)) for x, y in tubule_positions]

    # Subtract cylinders from the cube
    for pos_x, pos_y in jittered_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        tubule_object = bpy.context.object

        # Create Boolean modifier to subtract the tubule from the cube
        bool_modifier = cube_object.modifiers.new(name=f"Boolean_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule_object

        # Apply the Boolean modifier
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        # Remove the cylinder after the operation
        bpy.data.objects.remove(tubule_object, do_unlink=True)

# Create the tubular structure with noise
generate_tubules(number_of_tubules, max_noise)
