# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_blender_code_that_constructs_a_helical_stacked_bioinspired_material_with" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a blender code that constructs a helical stacked bioinspired material with noise.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical design
ply_count = 9
angle_increment = 8
noise_enabled = True
max_noise_deviation = 7

def add_cube_at_height(index):
    cube_size = 2
    total_height = 2
    single_ply_height = total_height / ply_count
    z_coord = index * single_ply_height

    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_coord))
    current_cube = bpy.context.object
    current_cube.scale[2] = single_ply_height / 2

    return current_cube

for i in range(ply_count):
    cube = add_cube_at_height(i)
    base_rotation = i * angle_increment
    if noise_enabled:
        base_rotation += random.uniform(-max_noise_deviation, max_noise_deviation)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = cube
    cube.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(base_rotation), orient_axis='Z')
