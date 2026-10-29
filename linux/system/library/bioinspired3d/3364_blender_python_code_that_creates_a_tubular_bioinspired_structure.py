# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_creates_a_tubular_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that creates a tubular bioinspired structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Specify total tubules
total_tubules = 12

def generate_tubules():
    # Function to create a cube and subtract tubules
    # 1. Create a cube as the main object.
    # 2. Compute positions for tubules.
    # 3. Use Boolean modifier to subtract tubules.
    
    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    # Calculate the grid size
    grid_size = math.ceil(math.sqrt(total_tubules))
    offset = 2 / grid_size
    start = -1 + offset / 2
    
    # Determine positions for each tubule
    positions = [(start + (i % grid_size) * offset,
                   start + (i // grid_size) * offset)
                  for i in range(total_tubules)]
    
    # Create and subtract tubules
    for pos_x, pos_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        current_tubule = bpy.context.object
        
        # Apply Boolean modifier
        bool_mod = main_cube.modifiers.new(name=f"Remove_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = current_tubule
        
        # Apply the modifier to perform subtraction
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        # Delete the tubule after subtraction
        bpy.data.objects.remove(current_tubule, do_unlink=True)

# Execute the creation of tubules
generate_tubules()
