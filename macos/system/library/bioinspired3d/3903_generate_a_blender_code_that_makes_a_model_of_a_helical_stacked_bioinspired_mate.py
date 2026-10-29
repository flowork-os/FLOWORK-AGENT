# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_blender_code_that_makes_a_model_of_a_helical_stacked_bioinspired_mate" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a blender code that makes a model of a helical stacked bioinspired material with noise in each rotation. think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
layers_count = 10  # Total number of layers
angle_increment = 15  # Degrees of rotation for each layer
noise_enabled = True  # Toggle noise in rotation
random_noise = 5  # Max deviation in degrees

# Function to generate a single layer of the helical structure
def generate_layer(layer_index):
    height = 2
    size = 2
    thickness = height / layers_count
    z_position = layer_index * thickness

    # Add a cube for the layer
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = thickness / 2

    # Calculate the rotation with potential noise
    rotation_angle = layer_index * angle_increment
    if noise_enabled:
        rotation_angle += random.uniform(-random_noise, random_noise)

    # Deselect all and select the current layer for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    # Rotate the layer around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
    return layer

# Build the helical structure
for index in range(layers_count):
    generate_layer(index)
