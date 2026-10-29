# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_code__build_a_model_of_a_helical_stacked_structure_with_randomness" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender code, build a model of a helical stacked structure with randomness in rotation. think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_num = 15
rotation_angle = 3
is_noise_enabled = True
noise_strength = 6

def create_helical_structure(index):
    height_total = 2
    cube_size = 2
    layer_thickness = height_total / layer_num
    z_coordinate = index * layer_thickness

    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_coordinate))
    helical_layer = bpy.context.object
    helical_layer.scale[2] = layer_thickness / 2

    base_rotation = index * rotation_angle
    if is_noise_enabled:
        base_rotation += random.uniform(-noise_strength, noise_strength)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = helical_layer
    helical_layer.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(base_rotation), orient_axis='Z')
    return helical_layer

for i in range(layer_num):
    create_helical_structure(i)
