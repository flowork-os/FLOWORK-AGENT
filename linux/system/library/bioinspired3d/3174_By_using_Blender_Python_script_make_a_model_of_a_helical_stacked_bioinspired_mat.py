# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_Python_script_make_a_model_of_a_helical_stacked_bioinspired_mat" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender Python script make a model of a helical stacked bioinspired material with rotational noise

import bpy
import math
import random

# Cleanup existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical model
layers = 15
rotation_angle = 4
apply_noise = True
noise_variation = 3

def helical_model(layer_count, rotation_angle, apply_noise):
    for i in range(layer_count):
        create_helical_segment(i, rotation_angle, apply_noise)

def create_helical_segment(index, rotation_angle, apply_noise):
    height = 2
    cube_size = 2
    segment_height = height / layers
    z_offset = index * segment_height

    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_offset))
    segment = bpy.context.object
    segment.scale[2] = segment_height / 2

    angle = index * rotation_angle
    if apply_noise:
        angle += random.uniform(-noise_variation, noise_variation)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = segment
    segment.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(angle), orient_axis='Z')

# Build the helical model
helical_model(layers, rotation_angle, apply_noise)
