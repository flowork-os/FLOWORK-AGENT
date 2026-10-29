# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_Blender_Python_script_that_builds_a_model_of_a_helical_stacked_material_wi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write Blender Python script that builds a model of a helical stacked material with angular variation per ply.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical structure
layer_count = 15
rotation_step = 5
noise_enabled = True
noise_range = 6

def add_cube_at_height(index, total_layers):
    height = 2
    cube_size = 2
    thickness = height / total_layers
    z_position = index * thickness

    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
    return bpy.context.object

for i in range(layer_count):
    cube = add_cube_at_height(i, layer_count)
    cube.scale[2] = (2 / layer_count) / 2

    rotation_angle = i * rotation_step
    if noise_enabled:
        rotation_angle += random.uniform(-noise_range, noise_range)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = cube
    cube.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
