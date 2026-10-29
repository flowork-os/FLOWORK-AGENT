# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_to_create_a_tubular_porous_bioinspired_structure__Think_step_by_s" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code to create a tubular porous bioinspired structure. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

total_tubules = 12

def generate_tubules():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(total_tubules))
    offset = 2 / grid_size
    start = -1 + offset / 2
    
    positions = [(start + (i % grid_size) * offset,
                   start + (i // grid_size) * offset)
                  for i in range(total_tubules)]
    
    for pos_x, pos_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        current_tubule = bpy.context.object
        
        bool_mod = main_cube.modifiers.new(name=f"Remove_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = current_tubule
        
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        bpy.data.objects.remove(current_tubule, do_unlink=True)

generate_tubules()
