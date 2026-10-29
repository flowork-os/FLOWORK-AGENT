# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_Blender_Python_script_create_a_helical_bioinspired_structure_with_rotat" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using Blender Python script create a helical bioinspired structure with rotational noise.

import bpy
import math
import random

# Clear the Blender scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure configuration
total_plies = 15  # Total number of plies
rotation_increment = 4  # Degrees of rotation for each ply
noise_enabled = False  # Disable noise
max_noise_value = 3  # Maximum noise in degrees

def generate_helical_structure(index):
    # Function to create a single helical structure component
    height_per_ply = 2.0 / total_plies
    z_coordinate = index * height_per_ply

    # Add a cube to the scene
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_coordinate))
    helical_part = bpy.context.object
    helical_part.scale[2] = height_per_ply / 2

    # Calculate rotation angle
    angle = index * rotation_increment
    if noise_enabled:
        angle += random.uniform(-max_noise_value, max_noise_value)

    # Deselect all objects and select the new part
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = helical_part
    helical_part.select_set(True)

    # Rotate around Z-axis
    bpy.ops.transform.rotate(value=math.radians(angle), orient_axis='Z')
    return helical_part

# Create the helical structure
for i in range(total_plies):
    generate_helical_structure(i)
