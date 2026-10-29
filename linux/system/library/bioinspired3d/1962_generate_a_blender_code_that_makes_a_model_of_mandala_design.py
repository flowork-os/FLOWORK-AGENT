# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_blender_code_that_makes_a_model_of_mandala_design" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a blender code that makes a model of mandala design.

import bpy
import math

def clear_scene():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

def create_shape(shape_type, x, y, height):
    if shape_type == 'triangle':
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.1, depth=height, location=(x, y, 0))
    elif shape_type == 'square':
        bpy.ops.mesh.primitive_cube_add(size=0.2, location=(x, y, 0))
    elif shape_type == 'circle':
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=height, location=(x, y, 0))

clear_scene()

for radius, count, shape in [(1, 8, 'triangle'), (2, 16, 'square'), (3, 24, 'circle'), (4, 32, 'triangle'), (5, 40, 'square')]:
    angle_step = 2 * math.pi / count
    for i in range(count):
        angle = i * angle_step
        x_coord = radius * math.cos(angle)
        y_coord = radius * math.sin(angle)
        create_shape(shape, x_coord, y_coord, height=0.1)

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0, 0, 0))
central_object = bpy.context.object
central_object.name = 'Center'
