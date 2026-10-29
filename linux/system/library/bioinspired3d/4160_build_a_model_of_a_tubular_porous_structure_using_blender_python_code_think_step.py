# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_a_tubular_porous_structure_using_blender_python_code_think_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of a tubular porous structure using blender python code think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_cylinders = 16

def build_structure():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(num_cylinders))
    spacing_distance = 2 / grid_dimension
    offset_start = -1 + spacing_distance / 2
    
    cylinder_positions = [(offset_start + (i % grid_dimension) * spacing_distance,
                           offset_start + (i // grid_dimension) * spacing_distance)
                          for i in range(num_cylinders)]
    
    for pos in cylinder_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos[0], pos[1], 0))
        cylinder = bpy.context.object

        bool_modifier = base_cube.modifiers.new(name=f"Subtract_{pos[0]}_{pos[1]}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = cylinder

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        bpy.data.objects.remove(cylinder, do_unlink=True)

build_structure()
