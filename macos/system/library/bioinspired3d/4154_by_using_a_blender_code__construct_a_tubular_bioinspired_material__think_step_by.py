# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_blender_code__construct_a_tubular_bioinspired_material__think_step_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a blender code, construct a tubular bioinspired material. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_cylinders = 9

def build_structure():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    
    grid_length = math.ceil(math.sqrt(num_cylinders))
    spacing_distance = 2 / grid_length
    initial_position = -1 + spacing_distance / 2

    for index in range(num_cylinders):
        x_coord = initial_position + (index % grid_length) * spacing_distance
        y_coord = initial_position + (index // grid_length) * spacing_distance
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x_coord, y_coord, 0))
        cylinder = bpy.context.object

        bool_op = cube_object.modifiers.new(name=f"Remove_{index}", type='BOOLEAN')
        bool_op.operation = 'DIFFERENCE'
        bool_op.object = cylinder

        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=bool_op.name)

        bpy.data.objects.remove(cylinder, do_unlink=True)

build_structure()
