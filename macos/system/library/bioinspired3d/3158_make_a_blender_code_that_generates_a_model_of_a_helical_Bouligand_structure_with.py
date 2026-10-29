# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_blender_code_that_generates_a_model_of_a_helical_Bouligand_structure_with" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a blender code that generates a model of a helical Bouligand structure with rotational noise

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical model
num_layers = 8  # Total layers in the helical formation
rotation_angle = 10  # Rotation angle for each layer

# Randomness parameters
include_noise = True  # Whether to include noise in rotation
noise_amount = 7  # Maximum noise in degrees

def add_helical_layer(index):
    # Function to create a helical layer with optional noise.
    total_height = 2
    layer_size = 2
    layer_thickness = total_height / num_layers
    z_position = index * layer_thickness

    # Create a cube at the calculated position
    bpy.ops.mesh.primitive_cube_add(size=layer_size, location=(0, 0, z_position))
    layer_cube = bpy.context.object
    layer_cube.scale[2] = layer_thickness / 2

    # Calculate the base rotation angle
    rotation_value = index * rotation_angle
    if include_noise:
        rotation_value += random.uniform(-noise_amount, noise_amount)

    # Select the newly created layer for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_cube
    layer_cube.select_set(True)

    # Perform rotation
    bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')
    return layer_cube

# Construct the helical formation
for i in range(num_layers):
    add_helical_layer(i)
