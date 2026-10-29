# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_code_construct_a_model_of_a_helical_Bouligand_material_with_rotati" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender code construct a model of a helical Bouligand material with rotational noise. think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical structure parameters
layers = 9
angle_increment = 8
apply_noise = True
noise_degree = 7

def build_helical_structure(num_layers):
    for idx in range(num_layers):
        add_layer(idx)

def add_layer(index):
    height = 2
    cube_size = 2
    layer_height = height / layers
    z_pos = index * layer_height

    bpy.ops.mesh.primitive_cube_add(
        size=cube_size,
        location=(0, 0, z_pos)
    )

    layer = bpy.context.object
    layer.scale[2] = layer_height / 2

    rotation_angle = index * angle_increment
    if apply_noise:
        rotation_angle += random.uniform(-noise_degree, noise_degree)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

build_helical_structure(layers)
