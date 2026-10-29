# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_Python_script_generate_a_helical_Bouligand_bioinspired_structur" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender Python script generate a helical Bouligand bioinspired structure with angular variation per ply Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical structure
layers = 6
angle_per_layer = 8
add_noise = True
noise_limit = 3

def build_helical_layers(num_layers, angle, noise):
    for idx in range(num_layers):
        z_value = (idx * 2) / num_layers
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_value))
        current_object = bpy.context.object
        current_object.scale[2] = (2 / num_layers) / 2

        rotation_value = idx * angle
        if add_noise:
            rotation_value += random.uniform(-noise, noise)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = current_object
        current_object.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')

build_helical_layers(layers, angle_per_layer, noise_limit)
