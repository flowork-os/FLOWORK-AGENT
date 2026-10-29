# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_to_generate_a_helical_bioinspired_material_with_noise_in_eac" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code to generate a helical bioinspired material with noise in each rotation think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 7
rotation_step = 10
add_noise = True
noise_range = 3

def build_helical_model(layer_count):
    for index in range(layer_count):
        add_layer(index)

def add_layer(idx):
    height = 2
    size = 2
    layer_height = height / layer_count
    z_coord = idx * layer_height

    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_coord))
    new_layer = bpy.context.object
    new_layer.scale[2] = layer_height / 2

    rotation_value = idx * rotation_step
    if add_noise:
        rotation_value += random.uniform(-noise_range, noise_range)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = new_layer
    new_layer.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')

build_helical_model(layer_count)
