# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_python_code_that_builds_a_model_of_a_helical_stacked_bioinspired_m" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender python code that builds a model of a helical stacked bioinspired material with noise

import bpy
import math
import random

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical structure parameters
ply_count = 12  # Total plies in the structure
rotation_angle = 20  # Rotation per ply in degrees
noise_included = True  # Toggle noise
noise_variance = 6  # Noise variation in degrees

def add_helical_layer(index):
    # Generate a single layer of the helical structure
    total_height = 2
    cube_dimensions = 2
    thickness = total_height / ply_count
    vertical_position = index * thickness

    # Create a cube at the specified vertical position
    bpy.ops.mesh.primitive_cube_add(size=cube_dimensions, location=(0, 0, vertical_position))
    layer = bpy.context.object
    layer.scale[2] = thickness / 2

    # Determine the rotation angle
    current_rotation = index * rotation_angle
    if noise_included:
        current_rotation += random.uniform(-noise_variance, noise_variance)

    # Deselect all and select the current layer
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    # Rotate the layer
    bpy.ops.transform.rotate(value=math.radians(current_rotation), orient_axis='Z')

# Create the helical structure
for i in range(ply_count):
    add_helical_layer(i)
