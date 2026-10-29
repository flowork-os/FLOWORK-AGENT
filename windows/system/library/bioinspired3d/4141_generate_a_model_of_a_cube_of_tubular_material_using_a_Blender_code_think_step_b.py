# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_a_cube_of_tubular_material_using_a_Blender_code_think_step_b" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of a cube of tubular material using a Blender code think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 16

def generate_tubules():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(num_tubules)]
    
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        current_tubule = bpy.context.object
        bool_modifier = main_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = current_tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(current_tubule, do_unlink=True)

generate_tubules()
