# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_Blender_Python_script_that_generates_a_tubular_structure_think_step_by_st" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create Blender Python script that generates a tubular structure think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 16

def build_tubules():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(num_tubules))
    interval = 2 / grid_dim
    initial_offset = -1 + interval / 2
    
    tubule_positions = [(initial_offset + (i % grid_dim) * interval,
                         initial_offset + (i // grid_dim) * interval)
                        for i in range(num_tubules)]
    
    for pos_x, pos_y in tubule_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        current_tubule = bpy.context.object

        bool_mod = base_cube.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = current_tubule

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        bpy.data.objects.remove(current_tubule, do_unlink=True)

build_tubules()
