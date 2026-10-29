# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_tubular_material_in_python_blender_code_Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a tubular material in python blender code Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubes = 16

def build_tubular_structure():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(num_tubes))
    tube_spacing = 2 / grid_dim
    initial_offset = -1 + tube_spacing / 2
    
    tubule_positions = [(initial_offset + (i % grid_dim) * tube_spacing, 
                          initial_offset + (i // grid_dim) * tube_spacing) 
                         for i in range(num_tubes)]
    
    for pos_x, pos_y in tubule_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        current_tubule = bpy.context.object

        bool_modifier = base_cube.modifiers.new(name=f"Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = current_tubule

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        bpy.data.objects.remove(current_tubule, do_unlink=True)

build_tubular_structure()
