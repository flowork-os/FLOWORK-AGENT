# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_script__build_a_helical_bioinspired_material_with_randomness_in_rot" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender script, build a helical bioinspired material with randomness in rotation think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_number = 14
rotation_step = 8
add_noise = True
noise_range = 7

def generate_layers():
    for index in range(layer_number):
        create_layer(index)

def create_layer(index):
    height = 2
    size = 2
    layer_thickness = height / layer_number
    z_position = index * layer_thickness

    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = layer_thickness / 2

    current_rotation = index * rotation_step
    if add_noise:
        current_rotation += random.uniform(-noise_range, noise_range)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(current_rotation), orient_axis='Z')

generate_layers()
