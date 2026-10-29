# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_a_cube_of_tubular_material_in_a_blender_code_think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of a cube of tubular material in a blender code think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

tubes_count = 12

def generate_structure():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object

    grid_size = math.ceil(math.sqrt(tubes_count))
    spacing = 2 / grid_size
    start = -1 + spacing / 2

    for i in range(tubes_count):
        pos_x = start + (i % grid_size) * spacing
        pos_y = start + (i // grid_size) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        tube = bpy.context.object

        bool_modifier = main_cube.modifiers.new(name=f"Subtract_{i}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tube

        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        bpy.data.objects.remove(tube, do_unlink=True)

generate_structure()
