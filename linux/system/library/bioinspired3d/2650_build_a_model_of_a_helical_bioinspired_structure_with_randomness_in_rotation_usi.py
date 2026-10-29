# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_a_helical_bioinspired_structure_with_randomness_in_rotation_usi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of a helical bioinspired structure with randomness in rotation using blender script think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical model
layers = 12  # Total number of layers
angle_increment = 10  # Degrees of rotation for each layer
add_noise = True  # Enable noise in rotation
noise_variation = 6  # Maximum noise in degrees

# Function to create a single layer
def add_layer(i):
    layer_height = 2 / layers
    z_pos = i * layer_height

    # Add cube at specified position
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_pos))
    cube = bpy.context.object
    cube.scale[2] = layer_height / 2

    # Calculate rotation
    rotation = i * angle_increment
    if add_noise:
        rotation += random.uniform(-noise_variation, noise_variation)

    # Deselect all, select the new cube, and rotate
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = cube
    cube.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(rotation), orient_axis='Z')

# Create the helical structure
for layer_index in range(layers):
    add_layer(layer_index)
