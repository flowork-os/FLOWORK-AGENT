# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_python_blender_code_that_creates_a_model_of_a_helical_twisted_ply_bioinsp" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create python blender code that creates a model of a helical twisted ply bioinspired structure with randomness in rotation Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layers = 15
rotation_increment = 4
enable_noise = True
max_deviation = 8

def create_helical_layers(num_layers):
    for layer_index in range(num_layers):
        create_layer(layer_index)

def create_layer(index):
    layer_height = 2 / layers
    z_position = index * layer_height

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    layer_object = bpy.context.object
    layer_object.scale[2] = layer_height / 2

    rotation_angle = index * rotation_increment
    if enable_noise:
        rotation_angle += random.uniform(-max_deviation, max_deviation)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_object
    layer_object.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')

create_helical_layers(layers)
