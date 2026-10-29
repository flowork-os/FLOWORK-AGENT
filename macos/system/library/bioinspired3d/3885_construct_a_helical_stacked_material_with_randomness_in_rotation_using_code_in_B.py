# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_helical_stacked_material_with_randomness_in_rotation_using_code_in_B" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a helical stacked material with randomness in rotation using code in Blender Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 9
rotation_increment = 8
introduce_noise = True
noise_variation = 7

def build_helical_cubes():
    height = 2
    width = 2
    layer_thickness = height / layer_count

    for index in range(layer_count):
        z_position = index * layer_thickness
        bpy.ops.mesh.primitive_cube_add(size=width, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = layer_thickness / 2

        rotation_angle = index * rotation_increment
        if introduce_noise:
            rotation_angle += random.uniform(-noise_variation, noise_variation)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)

        bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')

build_helical_cubes()
