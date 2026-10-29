# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_code_construct_mandala_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender code construct mandala pattern.

import bpy
import math

# Clear the current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def generate_circle(radius, coords, label):
    bpy.ops.mesh.primitive_circle_add(radius=radius, location=coords)
    circle_entity = bpy.context.object
    circle_entity.name = label
    return circle_entity

def generate_triangle(radius, coords, angle, label):
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=radius, depth=0.1, location=coords, rotation=angle)
    triangle_entity = bpy.context.object
    triangle_entity.name = label
    return triangle_entity

def generate_petal(radius, coords, angle, label):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=coords, rotation=angle)
    bpy.ops.transform.resize(value=(0.5, 1, 0.1))
    petal_entity = bpy.context.object
    petal_entity.name = label
    return petal_entity

# Create the central circle
generate_circle(radius=1, coords=(0, 0, 0), label='Core Circle')

# Create the first layer of triangles
for i in range(8):
    theta = i * (math.pi / 4)
    x_pos = 1.5 * math.cos(theta)
    y_pos = 1.5 * math.sin(theta)
    generate_triangle(radius=0.5, coords=(x_pos, y_pos, 0), angle=(0, 0, theta), label=f'Triangle {i + 1}')

# Create the second layer of circles
for i in range(16):
    theta = i * (math.pi / 8)
    x_pos = 2.5 * math.cos(theta)
    y_pos = 2.5 * math.sin(theta)
    generate_circle(radius=0.3, coords=(x_pos, y_pos, 0), label=f'Circle {i + 1}')

# Create the third layer of petals
for i in range(16):
    theta = i * (math.pi / 8)
    x_pos = 3.5 * math.cos(theta)
    y_pos = 3.5 * math.sin(theta)
    generate_petal(radius=0.3, coords=(x_pos, y_pos, 0), angle=(0, 0, theta), label=f'Petal {i + 1}')
