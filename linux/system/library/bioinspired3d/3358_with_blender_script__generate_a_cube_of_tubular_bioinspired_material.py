# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_script__generate_a_cube_of_tubular_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender script, generate a cube of tubular bioinspired material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
count_of_tubules = 25  # Total number of tubules


def construct_tubules():
    # This function constructs a grid of tubules within a cube.
    # Steps:
    # 1. Create a cube.
    # 2. Position tubules in a grid.
    # 3. Use Boolean modifiers to cut out tubules from the cube.
    
    # Add a cube to the scene
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    # Calculate the grid size
    grid_dim = math.ceil(math.sqrt(count_of_tubules))
    spacing_dist = 2 / grid_dim
    offset_start = -1 + spacing_dist / 2
    
    # Generate positions for tubules
    positions_list = [(offset_start + (i % grid_dim) * spacing_dist,
                        offset_start + (i // grid_dim) * spacing_dist)
                       for i in range(count_of_tubules)]
    
    # Create and subtract tubules from the cube
    for pos_x, pos_y in positions_list:
        # Add a cylinder for the tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        tubule_object = bpy.context.object

        # Create Boolean modifier for the cube
        boolean_mod = main_cube.modifiers.new(name=f"Cut_{pos_x}_{pos_y}", type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = tubule_object

        # Apply the Boolean modifier
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)

        # Remove the cylinder post-subtraction
        bpy.data.objects.remove(tubule_object, do_unlink=True)

# Run the tubule construction
construct_tubules()
