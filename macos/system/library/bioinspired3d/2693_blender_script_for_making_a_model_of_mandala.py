# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_making_a_model_of_mandala" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for making a model of mandala.

import bpy
import math

# Clear all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to build a foundational mandala shape

def build_foundational_mandala():
    # Create a series of circles
    for i in range(8):
        angle = math.radians(i * 45)
        x_coord = 2 * math.cos(angle)
        y_coord = 2 * math.sin(angle)
        bpy.ops.mesh.primitive_circle_add(radius=0.5, location=(x_coord, y_coord, 0))

    # Generate triangles oriented at specific angles
    for i in range(8):
        angle = math.radians(i * 45 + 22.5)
        x_coord = 1.5 * math.cos(angle)
        y_coord = 1.5 * math.sin(angle)
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.5, depth=0.1, location=(x_coord, y_coord, 0), rotation=(0, 0, angle))

build_foundational_mandala()

# Function to create a detailed mandala

def build_detailed_mandala():
    # Create petal-like shapes
    for i in range(16):
        angle = math.radians(i * 22.5)
        x_coord = 3 * math.cos(angle)
        y_coord = 3 * math.sin(angle)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(x_coord, y_coord, 0))

    # Add spiral shapes
    for i in range(16):
        angle = math.radians(i * 22.5)
        x_coord = 1.5 * math.cos(angle)
        y_coord = 1.5 * math.sin(angle)
        bpy.ops.mesh.primitive_torus_add(location=(x_coord, y_coord, 0), rotation=(0, 0, angle))

    # Add interlocking cube shapes
    for i in range(8):
        angle = math.radians(i * 45)
        x_coord = 2 * math.cos(angle)
        y_coord = 2 * math.sin(angle)
        bpy.ops.mesh.primitive_cube_add(size=0.5, location=(x_coord, y_coord, 0), rotation=(0, 0, angle))

build_detailed_mandala()
