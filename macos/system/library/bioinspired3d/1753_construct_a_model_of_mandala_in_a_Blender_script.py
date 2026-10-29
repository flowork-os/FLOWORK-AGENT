# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_mandala_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of mandala in a Blender script

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def create_basic_structure():
    for j in range(8):
        radian_angle = math.radians(j * 45)
        pos_x = math.cos(radian_angle) * 2
        pos_y = math.sin(radian_angle) * 2
        bpy.ops.mesh.primitive_circle_add(radius=0.5, location=(pos_x, pos_y, 0))

    for j in range(8):
        radian_angle = math.radians(j * 45 + 22.5)
        pos_x = math.cos(radian_angle) * 1.5
        pos_y = math.sin(radian_angle) * 1.5
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.5, depth=0.1, location=(pos_x, pos_y, 0), rotation=(0, 0, radian_angle))

create_basic_structure()

def create_complex_structure():
    for j in range(16):
        radian_angle = math.radians(j * 22.5)
        pos_x = math.cos(radian_angle) * 3
        pos_y = math.sin(radian_angle) * 3
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(pos_x, pos_y, 0))

    for j in range(16):
        radian_angle = math.radians(j * 22.5)
        pos_x = math.cos(radian_angle) * 1.5
        pos_y = math.sin(radian_angle) * 1.5
        bpy.ops.mesh.primitive_torus_add(location=(pos_x, pos_y, 0), rotation=(0, 0, radian_angle))

    for j in range(8):
        radian_angle = math.radians(j * 45)
        pos_x = math.cos(radian_angle) * 2
        pos_y = math.sin(radian_angle) * 2
        bpy.ops.mesh.primitive_cube_add(size=0.5, location=(pos_x, pos_y, 0), rotation=(0, 0, radian_angle))

create_complex_structure()
