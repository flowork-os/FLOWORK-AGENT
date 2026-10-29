# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_generates_a_model_of_a_helical_bioinspired_structure_with" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that generates a model of a helical bioinspired structure with randomness in rotation.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical formation
layers_count = 10  # Total number of layers in the structure
angle_per_layer = 15  # Degrees of rotation for each layer

# Noise settings for rotation variation
apply_noise = True  # Toggle rotation noise
max_noise = 5  # Maximum random deviation in degrees

def generate_layer(layer_index):
    # Constructs a helical layer with optional noise.
    height = 2
    cube_size = 2
    layer_height = height / layers_count
    z_position = layer_index * layer_height

    # Add a cube mesh at the calculated position
    bpy.ops.mesh.primitive_cube_add(
        size=cube_size,
        location=(0, 0, z_position)
    )

    current_layer = bpy.context.object
    current_layer.scale[2] = layer_height / 2

    # Calculate rotation with noise
    rotation_angle = layer_index * angle_per_layer
    if apply_noise:
        rotation_angle += random.uniform(-max_noise, max_noise)

    # Deselect all and select the current layer for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    # Apply rotation around the Z-axis
    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )
    return current_layer

# Build the helical structure
for index in range(layers_count):
    generate_layer(index)
