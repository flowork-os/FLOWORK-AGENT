# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_script_make_a_model_of_a_tubular_structure_Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender script make a model of a tubular structure Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 16

def build_tubule_grid():
    base_cube = bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_obj = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(num_tubules))
    offset = 2 / grid_dim
    initial_offset = -1 + offset / 2
    
    tubule_positions = [
        (initial_offset + (i % grid_dim) * offset,
         initial_offset + (i // grid_dim) * offset)
        for i in range(num_tubules)
    ]
    
    for x, y in tubule_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule_cylinder = bpy.context.object
        
        boolean_mod = cube_obj.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = tubule_cylinder
        
        bpy.context.view_layer.objects.active = cube_obj
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)
        
        bpy.data.objects.remove(tubule_cylinder, do_unlink=True)

build_tubule_grid()
