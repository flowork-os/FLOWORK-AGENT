# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_to_build_a_helical_twisted_ply_material_with_randomness_in_rotati" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script to build a helical twisted ply material with randomness in rotation

import bpy
import math
import random

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical parameters
layer_count = 12
rotation_step = 8
enable_noise = True
noise_range = 7

def create_helical_structure(layer_count, rotation_step, enable_noise, noise_range):
    for layer_index in range(layer_count):
        create_single_layer(layer_index, rotation_step, enable_noise, noise_range)

def create_single_layer(layer_index, rotation_step, enable_noise, noise_range):
    height = 2
    size = 2
    layer_height = height / layer_count
    z_position = layer_index * layer_height

    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
    layer_object = bpy.context.object
    layer_object.scale[2] = layer_height / 2

    base_rotation = layer_index * rotation_step
    if enable_noise:
        base_rotation += random.uniform(-noise_range, noise_range)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_object
    layer_object.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(base_rotation), orient_axis='Z')

# Generate the helical structure
create_helical_structure(layer_count, rotation_step, enable_noise, noise_range)
