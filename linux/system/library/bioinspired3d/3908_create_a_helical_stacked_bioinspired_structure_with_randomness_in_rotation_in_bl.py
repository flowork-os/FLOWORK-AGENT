# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_helical_stacked_bioinspired_structure_with_randomness_in_rotation_in_bl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a helical stacked bioinspired structure with randomness in rotation in blender code think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helix configuration
ply_count = 12  # Number of plies in the helical design
rotation_step = 5  # Degrees of rotation per ply

# Noise configuration
activate_noise = True  # Enable noise in rotation
noise_deviation = 4  # Maximum noise in degrees

def create_helical_plates(index):
    # Function to create a helical plate with noise variation.
    total_height = 2
    plate_size = 2
    individual_thickness = total_height / ply_count
    z_position = index * individual_thickness

    # Add a cube at the specified height
    bpy.ops.mesh.primitive_cube_add(size=plate_size, location=(0, 0, z_position))
    current_plate = bpy.context.object
    current_plate.scale[2] = individual_thickness / 2

    # Calculate rotation angle with noise
    rotation_angle = index * rotation_step
    if activate_noise:
        rotation_angle += random.uniform(-noise_deviation, noise_deviation)

    # Prepare to rotate the plate
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = current_plate
    current_plate.select_set(True)

    # Rotate the plate around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
    return current_plate

# Generate the helical structure
for i in range(ply_count):
    create_helical_plates(i)
