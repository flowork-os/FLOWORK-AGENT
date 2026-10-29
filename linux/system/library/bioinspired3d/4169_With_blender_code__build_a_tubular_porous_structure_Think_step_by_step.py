# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_code__build_a_tubular_porous_structure_Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender code, build a tubular porous structure Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

cylinder_count = 9

def build_structure_with_cylinders():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(cylinder_count))
    interval = 2 / grid_dimension
    initial_position = -1 + interval / 2

    for i in range(cylinder_count):
        x_pos = initial_position + (i % grid_dimension) * interval
        y_pos = initial_position + (i // grid_dimension) * interval
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x_pos, y_pos, 0))
        cylinder_object = bpy.context.object
        
        boolean_modifier = cube_object.modifiers.new(name=f"Subtraction_{i}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = cylinder_object
        
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(cylinder_object, do_unlink=True)

build_structure_with_cylinders()
