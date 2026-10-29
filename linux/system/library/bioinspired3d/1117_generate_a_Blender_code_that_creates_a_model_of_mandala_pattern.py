# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_Blender_code_that_creates_a_model_of_mandala_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a Blender code that creates a model of mandala pattern

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to add a circular mesh

def add_circle(radius, position, identifier):
    bpy.ops.mesh.primitive_circle_add(radius=radius, location=position)
    circle_object = bpy.context.object
    circle_object.name = identifier
    return circle_object

# Function to add a triangular mesh

def add_triangle(radius, position, rotation_angle, identifier):
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=radius, depth=0.1, location=position, rotation=rotation_angle)
    triangle_object = bpy.context.object
    triangle_object.name = identifier
    return triangle_object

# Function to add a petal shape

def add_petal(radius, position, rotation_angle, identifier):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=position, rotation=rotation_angle)
    bpy.ops.transform.resize(value=(0.5, 1, 0.1))
    petal_object = bpy.context.object
    petal_object.name = identifier
    return petal_object

# Create the central circle
add_circle(radius=1, position=(0, 0, 0), identifier='Main Circle')

# Create the outer triangles
for index in range(8):
    theta = index * (math.pi / 4)
    x_coord = 1.5 * math.cos(theta)
    y_coord = 1.5 * math.sin(theta)
    add_triangle(radius=0.5, position=(x_coord, y_coord, 0), rotation_angle=(0, 0, theta), identifier=f'Triangle {index + 1}')

# Create the second layer of circles
for index in range(16):
    theta = index * (math.pi / 8)
    x_coord = 2.5 * math.cos(theta)
    y_coord = 2.5 * math.sin(theta)
    add_circle(radius=0.3, position=(x_coord, y_coord, 0), identifier=f'Circle {index + 1}')

# Create the third layer of petals
for index in range(16):
    theta = index * (math.pi / 8)
    x_coord = 3.5 * math.cos(theta)
    y_coord = 3.5 * math.sin(theta)
    add_petal(radius=0.3, position=(x_coord, y_coord, 0), rotation_angle=(0, 0, theta), identifier=f'Petal {index + 1}')
