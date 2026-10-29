# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_helical_Bouligand_bioinspired_structure_with_noise_in_each_rotation" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a helical Bouligand bioinspired structure with noise in each rotation in a blender code think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

total_plies = 15  # Total number of plies
rotation_increment = 4  # Degrees of rotation for each ply
noise_enabled = False  # Disable noise
max_noise_value = 3  # Maximum noise in degrees

def generate_helical_structure(index):
    height_per_ply = 2.0 / total_plies
    z_coordinate = index * height_per_ply

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_coordinate))
    helical_part = bpy.context.object
    helical_part.scale[2] = height_per_ply / 2

    angle = index * rotation_increment
    if noise_enabled:
        angle += random.uniform(-max_noise_value, max_noise_value)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = helical_part
    helical_part.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(angle), orient_axis='Z')
    return helical_part

for i in range(total_plies):
    generate_helical_structure(i)
