# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_code_in_Blender_that_makes_a_helical_stacked_material_with_randomness_in_r" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write code in Blender that makes a helical stacked material with randomness in rotation Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

plies_count = 12  # Total number of plies
rotation_step = 5  # Degrees of rotation for each ply
apply_noise = True  # Flag to apply noise
noise_degree = 6  # Maximum noise in degrees

def add_helical_plates(index):
    plate_height = 2.0 / plies_count
    z_location = index * plate_height

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_location))
    plate = bpy.context.object
    plate.scale[2] = plate_height / 2

    rotation_value = index * rotation_step
    if apply_noise:
        rotation_value += random.uniform(-noise_degree, noise_degree)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = plate
    plate.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')
    return plate

for i in range(plies_count):
    add_helical_plates(i)
