# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_Python_script_that_creates_mandala_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender Python script that creates mandala pattern.

import bpy
import math

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

class GeometryCreator:
    def __init__(self):
        pass

    @staticmethod
    def create_circle(radius, position, name):
        bpy.ops.mesh.primitive_circle_add(radius=radius, location=position)
        obj = bpy.context.object
        obj.name = name
        return obj

    @staticmethod
    def create_triangle(radius, position, rotation, name):
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=radius, depth=0.1, location=position, rotation=rotation)
        obj = bpy.context.object
        obj.name = name
        return obj

    @staticmethod
    def create_petal(radius, position, rotation, name):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=position, rotation=rotation)
        bpy.ops.transform.resize(value=(0.5, 1, 0.1))
        obj = bpy.context.object
        obj.name = name
        return obj

# Instantiate the creator class
creator = GeometryCreator()

# Create the main circle
creator.create_circle(radius=1, position=(0, 0, 0), name='Base Circle')

# Create triangles in the first layer
for idx in range(8):
    angle = idx * (math.pi / 4)
    x_pos = 1.5 * math.cos(angle)
    y_pos = 1.5 * math.sin(angle)
    creator.create_triangle(radius=0.5, position=(x_pos, y_pos, 0), rotation=(0, 0, angle), name=f'Triangle {idx + 1}')

# Create circles in the second layer
for idx in range(16):
    angle = idx * (math.pi / 8)
    x_pos = 2.5 * math.cos(angle)
    y_pos = 2.5 * math.sin(angle)
    creator.create_circle(radius=0.3, position=(x_pos, y_pos, 0), name=f'Circle {idx + 1}')

# Create petals in the third layer
for idx in range(16):
    angle = idx * (math.pi / 8)
    x_pos = 3.5 * math.cos(angle)
    y_pos = 3.5 * math.sin(angle)
    creator.create_petal(radius=0.3, position=(x_pos, y_pos, 0), rotation=(0, 0, angle), name=f'Petal {idx + 1}')
