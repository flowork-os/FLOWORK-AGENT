# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_constructs_a_model_of_a_helical_Bouligand_material_wi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that constructs a model of a helical Bouligand material with noise in each rotation think step by step

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
