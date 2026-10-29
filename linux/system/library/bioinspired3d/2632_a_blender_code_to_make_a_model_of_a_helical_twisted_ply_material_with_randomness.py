# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_to_make_a_model_of_a_helical_twisted_ply_material_with_randomness" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code to make a model of a helical twisted ply material with randomness in rotation. Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for creating the helical model
layers = 15
rotation_angle = 4
add_random_noise = True
noise_range = 3

def build_helical_structure(layer_count):
    for layer_index in range(layer_count):
        create_helical_layer(layer_index)

def create_helical_layer(index):
    cube_size = 2
    total_height = 2
    layer_height = total_height / layers
    z_position = index * layer_height

    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
    new_cube = bpy.context.object
    new_cube.scale[2] = layer_height / 2

    rotation_value = index * rotation_angle
    if add_random_noise:
        rotation_value += random.uniform(-noise_range, noise_range)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = new_cube
    new_cube.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')

# Execute the helical structure creation
build_helical_structure(layers)
