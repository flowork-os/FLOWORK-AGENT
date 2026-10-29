# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_code__make_a_helical_stacked_material_with_angular_variation" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender code, make a helical stacked material with angular variation per ply Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_total = 15
rotation_angle = 4
apply_randomness = True
random_strength = 3

def create_helical_layer(layer_index):
    height = 2
    size = 2
    thickness = height / layer_total
    z_position = layer_index * thickness

    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = thickness / 2

    rotation = layer_index * rotation_angle
    if apply_randomness:
        rotation += random.uniform(-random_strength, random_strength)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(rotation), orient_axis='Z')

for i in range(layer_total):
    create_helical_layer(i)
