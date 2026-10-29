# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_that_generates_a_model_of_a_helical_twisted_ply_bioinspired_stru" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender that generates a model of a helical twisted ply bioinspired structure with rotational noise.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical model
layers_count = 10  # Total layers in the structure
angle_increment = 15  # Degrees of rotation for each layer

# Randomness settings for rotation
apply_randomness = True  # Toggle for rotation randomness
max_random_deviation = 5  # Max deviation from base angle

def generate_layer(index):
    # Generates a single layer of the helical structure.
    height_per_layer = 2 / layers_count
    z_position = index * height_per_layer

    # Create a cube at the specified position
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = height_per_layer / 2

    # Calculate the rotation angle
    rotation_angle = index * angle_increment
    if apply_randomness:
        rotation_angle += random.uniform(-max_random_deviation, max_random_deviation)

    # Deselect all and select the current layer for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    # Rotate the layer around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
    return layer

# Build the helical structure
for i in range(layers_count):
    generate_layer(i)
