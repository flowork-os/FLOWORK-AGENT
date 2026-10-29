# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_a_helical_Bouligand_material_with_noise_using_python_blender_c" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of a helical Bouligand material with noise using python blender code

import bpy
import math
import random

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure specifications
plies_count = 12  # Total number of plies
rotation_step = 5  # Degrees of rotation for each ply
apply_noise = True  # Flag to apply noise
noise_degree = 6  # Maximum noise in degrees

def add_helical_plates(index):
    # Function to create a helical plate
    plate_height = 2.0 / plies_count
    z_location = index * plate_height

    # Create the plate
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_location))
    plate = bpy.context.object
    plate.scale[2] = plate_height / 2

    # Determine the base rotation
    rotation_value = index * rotation_step
    if apply_noise:
        rotation_value += random.uniform(-noise_degree, noise_degree)

    # Deselect all and select the plate
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = plate
    plate.select_set(True)

    # Rotate the plate around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')
    return plate

# Create the helical structure
for i in range(plies_count):
    add_helical_plates(i)
