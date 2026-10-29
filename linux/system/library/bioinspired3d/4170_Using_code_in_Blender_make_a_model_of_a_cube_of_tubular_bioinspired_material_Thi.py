# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_code_in_Blender_make_a_model_of_a_cube_of_tubular_bioinspired_material_Thi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using code in Blender make a model of a cube of tubular bioinspired material Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubes = 16  # Chosen number of tubules

def generate_tubes():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubes))
    spacing = 2 / grid_size
    initial_offset = -1 + spacing / 2
    
    tube_positions = [(initial_offset + (i % grid_size) * spacing,
                       initial_offset + (i // grid_size) * spacing) 
                      for i in range(num_tubes)]
    
    for x, y in tube_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object
        bool_modifier = main_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tube
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tube, do_unlink=True)

generate_tubes()
