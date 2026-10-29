# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_script__construct_a_tubular_porous_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender script, construct a tubular porous bioinspired structure

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set the number of tubes in the structure
number_of_tubules = 16

def generate_tubular_structure():
    # Construct a cube and subtract tubules from it.
    # Steps:
    # 1. Create a base cube.
    # 2. Calculate positions for the tubules.
    # 3. Subtract each tubule from the cube using Boolean modifiers.

    # Create a cube to start with
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object

    # Determine the grid size for tubule arrangement
    grid_dimension = math.ceil(math.sqrt(number_of_tubules))
    spacing_distance = 2 / grid_dimension
    offset = -1 + spacing_distance / 2

    # Calculate positions for each tubule
    tubule_positions = [
        (offset + (i % grid_dimension) * spacing_distance,
         offset + (i // grid_dimension) * spacing_distance)
        for i in range(number_of_tubules)
    ]

    # Subtract each tubule from the cube
    for pos_x, pos_y in tubule_positions:
        # Add a cylinder at the given position
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        current_tubule = bpy.context.object

        # Create a Boolean modifier to subtract the tubule
        bool_modifier = base_cube.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = current_tubule

        # Apply the Boolean modifier
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        # Delete the tubule object
        bpy.data.objects.remove(current_tubule, do_unlink=True)

# Execute the tubule generation function
generate_tubular_structure()
