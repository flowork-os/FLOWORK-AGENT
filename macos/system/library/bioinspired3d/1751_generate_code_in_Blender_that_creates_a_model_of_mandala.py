# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_code_in_Blender_that_creates_a_model_of_mandala" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate code in Blender that creates a model of mandala.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def generate_basic_mandala():
    for index in range(8):
        theta = math.radians(index * 45)
        pos_x = math.cos(theta) * 2
        pos_y = math.sin(theta) * 2
        bpy.ops.mesh.primitive_circle_add(radius=0.5, location=(pos_x, pos_y, 0))

    for index in range(8):
        theta = math.radians(index * 45 + 22.5)
        pos_x = math.cos(theta) * 1.5
        pos_y = math.sin(theta) * 1.5
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.5, depth=0.1, location=(pos_x, pos_y, 0), rotation=(0, 0, theta))

generate_basic_mandala()

def generate_intricate_mandala():
    for index in range(16):
        theta = math.radians(index * 22.5)
        pos_x = math.cos(theta) * 3
        pos_y = math.sin(theta) * 3
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(pos_x, pos_y, 0))

    for index in range(16):
        theta = math.radians(index * 22.5)
        pos_x = math.cos(theta) * 1.5
        pos_y = math.sin(theta) * 1.5
        bpy.ops.mesh.primitive_torus_add(location=(pos_x, pos_y, 0), rotation=(0, 0, theta))

    for index in range(8):
        theta = math.radians(index * 45)
        pos_x = math.cos(theta) * 2
        pos_y = math.sin(theta) * 2
        bpy.ops.mesh.primitive_cube_add(size=0.5, location=(pos_x, pos_y, 0), rotation=(0, 0, theta))

generate_intricate_mandala()
