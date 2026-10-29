# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_Blender_code_that_creates_a_model_of_mandala_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a Blender code that creates a model of mandala pattern

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def add_circle(radius, position, identifier):
    bpy.ops.mesh.primitive_circle_add(radius=radius, location=position)
    circle_object = bpy.context.object
    circle_object.name = identifier
    return circle_object

def add_triangle(radius, position, rotation_angle, identifier):
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=radius, depth=0.1, location=position, rotation=rotation_angle)
    triangle_object = bpy.context.object
    triangle_object.name = identifier
    return triangle_object

def add_petal(radius, position, rotation_angle, identifier):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=position, rotation=rotation_angle)
    bpy.ops.transform.resize(value=(0.5, 1, 0.1))
    petal_object = bpy.context.object
    petal_object.name = identifier
    return petal_object

add_circle(radius=1, position=(0, 0, 0), identifier='Main Circle')

for index in range(8):
    theta = index * (math.pi / 4)
    x_coord = 1.5 * math.cos(theta)
    y_coord = 1.5 * math.sin(theta)
    add_triangle(radius=0.5, position=(x_coord, y_coord, 0), rotation_angle=(0, 0, theta), identifier=f'Triangle {index + 1}')

for index in range(16):
    theta = index * (math.pi / 8)
    x_coord = 2.5 * math.cos(theta)
    y_coord = 2.5 * math.sin(theta)
    add_circle(radius=0.3, position=(x_coord, y_coord, 0), identifier=f'Circle {index + 1}')

for index in range(16):
    theta = index * (math.pi / 8)
    x_coord = 3.5 * math.cos(theta)
    y_coord = 3.5 * math.sin(theta)
    add_petal(radius=0.3, position=(x_coord, y_coord, 0), rotation_angle=(0, 0, theta), identifier=f'Petal {index + 1}')
