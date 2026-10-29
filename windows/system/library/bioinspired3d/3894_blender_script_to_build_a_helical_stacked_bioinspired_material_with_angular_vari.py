# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_to_build_a_helical_stacked_bioinspired_material_with_angular_vari" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script to build a helical stacked bioinspired material with angular variation per ply think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layers = 6  # Number of layers
ply_rotation = 8  # Degrees of rotation for each layer

is_noise_active = True  # Activate noise
noise_limit = 3  # Max noise in degrees

def make_helical_layers(num_layers):
    layer_height = 2 / num_layers
    for idx in range(num_layers):
        z_coord = idx * layer_height

        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_coord))
        layer = bpy.context.object
        layer.scale[2] = layer_height / 2

        rotation_angle = idx * ply_rotation
        if is_noise_active:
            rotation_angle += random.uniform(-noise_limit, noise_limit)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')

make_helical_layers(layers)
