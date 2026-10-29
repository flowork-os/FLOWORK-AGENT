# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_blender_code_that_creates_a_tubular_porous_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a blender code that creates a tubular porous bioinspired material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Specify the number of tubular structures
tube_count = 15  # Selected value for the number of tubules


def construct_tubular_grid():
    # Main function to build the grid of tubules
    # Process:
    # 1. Create a base cube.
    # 2. Position tubules in a grid pattern.
    # 3. Subtract tubules from the cube using Boolean operations.
    
    # Create a cube at the origin
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    # Calculate grid dimensions
    grid_dimensions = math.ceil(math.sqrt(tube_count))
    gap = 2 / grid_dimensions
    initial_pos = -1 + gap / 2
    
    # Generate positions for the tubules
    grid_positions = [(initial_pos + (i % grid_dimensions) * gap,
                        initial_pos + (i // grid_dimensions) * gap)
                       for i in range(tube_count)]
    
    # Create and subtract each tube from the cube
    for x_coord, y_coord in grid_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x_coord, y_coord, 0))
        tube = bpy.context.object

        # Create Boolean modifier to perform the subtraction
        boolean_mod = cube.modifiers.new(name=f"Subtract_{x_coord}_{y_coord}", type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = tube

        # Apply the Boolean modifier
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)

        # Remove the tube after the operation
        bpy.data.objects.remove(tube, do_unlink=True)

# Run the tubular grid construction
construct_tubular_grid()
