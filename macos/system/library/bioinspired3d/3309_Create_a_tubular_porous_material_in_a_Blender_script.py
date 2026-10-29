# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_tubular_porous_material_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a tubular porous material in a Blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set the number of tubules
num_tubulars = 18

def create_cuboid_with_tubules():
    # This function constructs a cube and removes tubules from it.
    # Steps:
    # 1. Create a cube.
    # 2. Generate positions for tubules.
    # 3. Apply Boolean modifiers to subtract tubules.
    
    # Add a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    
    # Determine grid for positioning tubules
    grid_length = math.ceil(math.sqrt(num_tubulars))
    spacing = 2 / grid_length
    offset_start = -1 + spacing / 2
    
    # Create positions for each tubule
    positions = [(offset_start + (i % grid_length) * spacing,
                   offset_start + (i // grid_length) * spacing)
                  for i in range(num_tubulars)]
    
    # Create and subtract each tubule
    for position in positions:
        x, y = position
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule_object = bpy.context.object
        bool_modifier = cube_object.modifiers.new(name=f"Sub_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule_object
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule_object, do_unlink=True)

# Call the function to create the structure
create_cuboid_with_tubules()
