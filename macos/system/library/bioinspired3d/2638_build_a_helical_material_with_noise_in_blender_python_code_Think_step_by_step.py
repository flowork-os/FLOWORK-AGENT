# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_helical_material_with_noise_in_blender_python_code_Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a helical material with noise in blender python code Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 15  # Number of layers
rotation_angle = 8  # Rotation angle in degrees
noise_enabled = True  # Enable random noise
noise_strength = 3  # Noise deviation

def add_layer(index):
    height = 2
    cube_size = 2
    layer_thickness = height / layer_count
    z_position = index * layer_thickness

    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
    current_layer = bpy.context.object
    current_layer.scale[2] = layer_thickness / 2

    rotation_value = index * rotation_angle
    if noise_enabled:
        rotation_value += random.uniform(-noise_strength, noise_strength)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')

for layer_index in range(layer_count):
    add_layer(layer_index)
