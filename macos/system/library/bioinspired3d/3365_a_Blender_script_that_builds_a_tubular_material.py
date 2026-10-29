# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_builds_a_tubular_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that builds a tubular material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the total number of tubules
number_of_tubules = 20

def create_structure():
    # Function to create a cube and subtract tubules
    # 1. Create the base cube.
    # 2. Calculate positions for the tubules.
    # 3. Use Boolean modifiers to create the structure.
    
    # Create the primary cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    # Determine grid size
    grid_count = math.ceil(math.sqrt(number_of_tubules))
    spacing = 2 / grid_count
    offset_start = -1 + spacing / 2
    
    # Calculate positions for tubules
    positions = [(offset_start + (i % grid_count) * spacing,
                   offset_start + (i // grid_count) * spacing)
                  for i in range(number_of_tubules)]
    
    # Subtract each tubule from the cube
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        # Create Boolean modifier
        bool_modifier = cube.modifiers.new(name=f"Cut_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        
        # Apply modifier to the cube
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        # Remove the tubule object
        bpy.data.objects.remove(tubule, do_unlink=True)

# Generate the structure
create_structure()
