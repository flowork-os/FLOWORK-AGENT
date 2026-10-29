# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_code_generate_a_model_of_a_helical_bioinspired_material_with" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender code generate a model of a helical bioinspired material with noise in each rotation think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

ply_count = 12  # Total plies in the structure
rotation_angle = 20  # Rotation per ply in degrees
noise_included = True  # Toggle noise
noise_variance = 6  # Noise variation in degrees

def add_helical_layer(index):
    total_height = 2
    cube_dimensions = 2
    thickness = total_height / ply_count
    vertical_position = index * thickness

    bpy.ops.mesh.primitive_cube_add(size=cube_dimensions, location=(0, 0, vertical_position))
    layer = bpy.context.object
    layer.scale[2] = thickness / 2

    current_rotation = index * rotation_angle
    if noise_included:
        current_rotation += random.uniform(-noise_variance, noise_variance)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(current_rotation), orient_axis='Z')

for i in range(ply_count):
    add_helical_layer(i)
