# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_script_that_makes_a_model_of_a_helical_Bouligand_bioinspired_st" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender script that makes a model of a helical Bouligand bioinspired structure with randomness in rotation Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure settings
layers = 6
rotation_angle = 20
random_rotation = True
rotation_noise = 3

def generate_helical_layers(layer_count):
    for index in range(layer_count):
        create_helical_layer(index)

def create_helical_layer(index):
    total_height = 2
    cube_size = 2
    layer_thickness = total_height / layers
    z_position = index * layer_thickness

    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
    current_layer = bpy.context.object
    current_layer.scale[2] = layer_thickness / 2

    base_rotation = index * rotation_angle
    if random_rotation:
        base_rotation += random.uniform(-rotation_noise, rotation_noise)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(base_rotation), orient_axis='Z')

generate_helical_layers(layers)
