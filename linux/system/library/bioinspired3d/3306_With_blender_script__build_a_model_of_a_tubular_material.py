# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_script__build_a_model_of_a_tubular_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender script, build a model of a tubular material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Number of tubes in the structure
num_tubes = 16

def build_tubular_grid():
    # This function constructs a grid of tubular shapes within a cube.
    # Steps:
    # 1. Create a cube.
    # 2. Position the tubes in a grid.
    # 3. Subtract tubes using Boolean modifiers.
    
    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    # Determine the grid size for the tubules
    grid_dimension = math.ceil(math.sqrt(num_tubes))
    tube_spacing = 2 / grid_dimension
    initial_offset = -1 + tube_spacing / 2
    
    # Calculate tube positions
    tube_locations = [(initial_offset + (i % grid_dimension) * tube_spacing,
                       initial_offset + (i // grid_dimension) * tube_spacing)
                      for i in range(num_tubes)]
    
    # Create and subtract each tube
    for pos in tube_locations:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object

        # Setup Boolean modifier for subtraction
        bool_mod = main_cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tube

        # Apply the Boolean modifier
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        # Delete the tube after subtraction
        bpy.data.objects.remove(tube, do_unlink=True)

# Execute the function to create the structure
build_tubular_grid()
