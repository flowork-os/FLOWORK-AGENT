# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_a_helical_stacked_structure_with_rotational_noise_in_Blender_c" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of a helical stacked structure with rotational noise in Blender code Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_layers = 12
angle_per_layer = 18
add_noise = True
noise_degree = 4

def create_helical_structure(layers):
    for layer_index in range(layers):
        create_layer(layer_index)

def create_layer(index):
    height = 2
    cube_size = 2
    layer_height = height / num_layers
    z_position = index * layer_height

    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
    current_layer = bpy.context.object
    current_layer.scale[2] = layer_height / 2

    base_rotation = index * angle_per_layer
    if add_noise:
        base_rotation += random.uniform(-noise_degree, noise_degree)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(base_rotation), orient_axis='Z')

create_helical_structure(num_layers)
