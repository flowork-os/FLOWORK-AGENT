# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_creates_a_helical_stacked_material_with_angular_variation_pe" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that creates a helical stacked material with angular variation per ply. think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_layers = 7  # Number of layers in the helical structure
rotation_angle = 10  # Angle of rotation for each layer
noise_enabled = True  # Toggle for noise in rotation
noise_amount = 4  # Maximum rotation noise

def create_helical_layer(index):
    layer_height = 2.0 / num_layers
    z_position = index * layer_height

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = layer_height / 2

    angle = index * rotation_angle
    if noise_enabled:
        angle += random.uniform(-noise_amount, noise_amount)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(angle), orient_axis='Z')
    return layer

for i in range(num_layers):
    create_helical_layer(i)
