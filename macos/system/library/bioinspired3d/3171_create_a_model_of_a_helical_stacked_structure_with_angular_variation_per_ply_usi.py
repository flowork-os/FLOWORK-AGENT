# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_a_helical_stacked_structure_with_angular_variation_per_ply_usi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of a helical stacked structure with angular variation per ply using a blender code

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
layers = 15  # Number of layers
rotation_step = 20  # Degrees per layer

# Noise configuration
randomize_rotation = True  # Should we introduce randomness?
max_random_deviation = 3  # Max random deviation in degrees

def add_layer(layer_index):
    # Function to add a layer to the helical structure.

    total_height = 2
    cube_size = 2
    layer_height = total_height / layers
    z_pos = layer_index * layer_height

    # Add a cube at the calculated position
    bpy.ops.mesh.primitive_cube_add(
        size=cube_size,
        location=(0, 0, z_pos)
    )

    layer_cube = bpy.context.object
    layer_cube.scale[2] = layer_height / 2

    # Calculate rotation
    rotation_value = layer_index * rotation_step
    if randomize_rotation:
        rotation_value += random.uniform(-max_random_deviation, max_random_deviation)

    # Deselect everything and select the new cube
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_cube
    layer_cube.select_set(True)

    # Rotate the cube
    bpy.ops.transform.rotate(
        value=math.radians(rotation_value),
        orient_axis='Z'
    )

# Build the helical structure
for index in range(layers):
    add_layer(index)
