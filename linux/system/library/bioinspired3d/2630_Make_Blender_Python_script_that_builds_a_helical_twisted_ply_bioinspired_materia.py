# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_Blender_Python_script_that_builds_a_helical_twisted_ply_bioinspired_materia" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make Blender Python script that builds a helical twisted ply bioinspired material with randomness in rotation. think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

ply_count = 15  # Number of plies
rotation_increment = 20  # Degrees of rotation per ply

enable_noise = True  # Enable noise
noise_level = 6  # Maximum noise in degrees

def add_helical_plates(count):
    height_per_ply = 2 / count
    for i in range(count):
        z_position = i * height_per_ply

        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
        plate = bpy.context.object
        plate.scale[2] = height_per_ply / 2

        rotation_angle = i * rotation_increment
        if enable_noise:
            rotation_angle += random.uniform(-noise_level, noise_level)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')

add_helical_plates(ply_count)
