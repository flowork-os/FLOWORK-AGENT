# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_a_tubular_porous_bioinspired_material_using_Blender_code_thi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of a tubular porous bioinspired material using Blender code think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

number_of_tubules = 16

def generate_tubular_structure():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object

    grid_dimension = math.ceil(math.sqrt(number_of_tubules))
    spacing_distance = 2 / grid_dimension
    offset = -1 + spacing_distance / 2

    tubule_positions = [
        (offset + (i % grid_dimension) * spacing_distance,
         offset + (i // grid_dimension) * spacing_distance)
        for i in range(number_of_tubules)
    ]

    for pos_x, pos_y in tubule_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        current_tubule = bpy.context.object

        bool_modifier = base_cube.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = current_tubule

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        bpy.data.objects.remove(current_tubule, do_unlink=True)

generate_tubular_structure()
