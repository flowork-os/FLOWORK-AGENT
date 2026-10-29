# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_helical_twisted_ply_bioinspired_material_with_rotational_noise_using_a" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a helical twisted ply bioinspired material with rotational noise using a Blender code think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 9
rotation_step = 8
noise_active = True
noise_range = 7

def add_layer(index, rotation_step, noise_active):
    height = 2
    cube_size = 2
    thickness = height / layer_count
    z_position = index * thickness

    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
    new_layer = bpy.context.object
    new_layer.scale[2] = thickness / 2

    rotation_angle = index * rotation_step
    if noise_active:
        rotation_angle += random.uniform(-noise_range, noise_range)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = new_layer
    new_layer.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')

for i in range(layer_count):
    add_layer(i, rotation_step, noise_active)
