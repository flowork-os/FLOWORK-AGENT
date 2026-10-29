# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_that_makes_a_model_of_a_tubular_porous_bioinspired_structure_think" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code that makes a model of a tubular porous bioinspired structure think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 20

def create_tubule_structure():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2

    for index in range(num_tubules):
        x = start_offset + (index % grid_size) * spacing
        y = start_offset + (index // grid_size) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        cylinder = bpy.context.object
        
        bool_mod = main_cube.modifiers.new(name=f"Bool_{index}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = cylinder
        
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(cylinder, do_unlink=True)

create_tubule_structure()
