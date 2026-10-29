# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_Blender_script_that_constructs_a_tubular_bioinspired_material_Think_ste" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a Blender script that constructs a tubular bioinspired material Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

total_tubules = 20

def tubule_grid():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2
    
    positions = [(offset + (i % grid_dim) * spacing,
                   offset + (i // grid_dim) * spacing) 
                  for i in range(total_tubules)]
    
    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object
        mod = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = tube
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(tube, do_unlink=True)

tubule_grid()
