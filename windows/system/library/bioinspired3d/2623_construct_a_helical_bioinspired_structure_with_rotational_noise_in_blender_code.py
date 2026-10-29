# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_helical_bioinspired_structure_with_rotational_noise_in_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a helical bioinspired structure with rotational noise in blender code think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_layers = 12
angle_step = 10
noise_active = True
noise_range = 6

def add_helical_layer(index):
    total_height = 2
    base_size = 2
    layer_height = total_height / num_layers
    z_coord = index * layer_height

    bpy.ops.mesh.primitive_cube_add(size=base_size, location=(0, 0, z_coord))
    new_layer = bpy.context.object
    new_layer.scale[2] = layer_height / 2

    angle = index * angle_step
    if noise_active:
        angle += random.uniform(-noise_range, noise_range)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = new_layer
    new_layer.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(angle), orient_axis='Z')
    return new_layer

for i in range(num_layers):
    add_helical_layer(i)
