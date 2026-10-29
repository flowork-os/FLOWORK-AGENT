# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_code_in_Blender__make_a_model_of_a_helical_twisted_ply_bioinspired_structur" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with code in Blender, make a model of a helical twisted ply bioinspired structure with rotational noise Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
num_layers = 12
angle_per_layer = 15
is_noise_enabled = True
noise_limit = 6

def create_helical_layers(layer_count, rotation_angle, noise):
    for i in range(layer_count):
        create_single_layer(i, rotation_angle, noise)

def create_single_layer(index, rotation_angle, noise):
    height = 2
    cube_size = 2
    layer_height = height / num_layers
    z_coord = index * layer_height

    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_coord))
    current_layer = bpy.context.object
    current_layer.scale[2] = layer_height / 2

    base_angle = index * rotation_angle
    if noise:
        base_angle += random.uniform(-noise_limit, noise_limit)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(base_angle), orient_axis='Z')

# Execute layer creation
create_helical_layers(num_layers, angle_per_layer, is_noise_enabled)
