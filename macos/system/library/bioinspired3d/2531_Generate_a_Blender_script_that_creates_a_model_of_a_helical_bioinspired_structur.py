# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_script_that_creates_a_model_of_a_helical_bioinspired_structur" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender script that creates a model of a helical bioinspired structure with randomness in rotation

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
layers_count = 10  # Total number of layers
angle_increment = 15  # Degrees of rotation for each layer

# Randomness settings for rotation
apply_noise = True  # Toggle noise effect
max_noise_deviation = 5  # Max deviation in degrees

# Function to generate each layer
def generate_layer(layer_index):
    height = 2
    cube_size = 2
    thickness = height / layers_count
    z_position = layer_index * thickness

    # Add cube mesh
    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = thickness / 2

    # Calculate rotation with potential noise
    rotation_angle = layer_index * angle_increment
    if apply_noise:
        rotation_angle += random.uniform(-max_noise_deviation, max_noise_deviation)

    # Select and rotate the layer
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
    return layer

# Build the helical structure
for index in range(layers_count):
    generate_layer(index)
