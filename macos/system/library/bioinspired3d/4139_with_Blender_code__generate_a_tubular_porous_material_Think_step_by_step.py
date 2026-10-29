# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_Blender_code__generate_a_tubular_porous_material_Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with Blender code, generate a tubular porous material Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubulars = 18

def create_cuboid_with_tubules():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    
    grid_length = math.ceil(math.sqrt(num_tubulars))
    spacing = 2 / grid_length
    offset_start = -1 + spacing / 2
    
    positions = [(offset_start + (i % grid_length) * spacing,
                   offset_start + (i // grid_length) * spacing)
                  for i in range(num_tubulars)]
    
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

create_cuboid_with_tubules()
