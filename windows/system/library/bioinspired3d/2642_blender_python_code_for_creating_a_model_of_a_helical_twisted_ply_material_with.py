# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_creating_a_model_of_a_helical_twisted_ply_material_with" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for creating a model of a helical twisted ply material with randomness in rotation. think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 15
rotation_angle = 5
noise_enabled = True
noise_limit = 3

def create_helical_layer(index):
    size = 2
    total_height = 2
    thickness = total_height / layer_count
    z_position = index * thickness

    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = thickness / 2

    angle = index * rotation_angle
    if noise_enabled:
        angle += random.uniform(-noise_limit, noise_limit)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(angle), orient_axis='Z')

for idx in range(layer_count):
    create_helical_layer(idx)
