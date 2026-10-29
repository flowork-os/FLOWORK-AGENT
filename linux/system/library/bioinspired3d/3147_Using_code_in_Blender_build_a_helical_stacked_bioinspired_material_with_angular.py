# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_code_in_Blender_build_a_helical_stacked_bioinspired_material_with_angular" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using code in Blender build a helical stacked bioinspired material with angular variation per ply.

import bpy
import math
import random

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helix parameters
ply_count = 15  # Number of plies
rotation_increment = 20  # Degrees of rotation per ply

# Noise parameters
enable_noise = True  # Enable noise
noise_level = 6  # Maximum noise in degrees

def add_helical_plates(count):
    height_per_ply = 2 / count
    for i in range(count):
        z_position = i * height_per_ply

        # Create the plate
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
        plate = bpy.context.object
        plate.scale[2] = height_per_ply / 2

        # Calculate rotation
        rotation_angle = i * rotation_increment
        if enable_noise:
            rotation_angle += random.uniform(-noise_level, noise_level)

        # Rotate the plate
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')

# Generate the helical structure
add_helical_plates(ply_count)
