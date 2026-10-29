# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_Python_script_that_creates_a_helical_twisted_ply_bioinspired_st" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender Python script that creates a helical twisted ply bioinspired structure with noise. think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical model
layers_count = 10  # Total layers in the model
angle_increment = 15  # Degrees of rotation for each layer
randomize_rotation = True  # Toggle for random rotation
max_random_offset = 5  # Max random offset in degrees

def generate_layer(layer_index):
    # Constructs a helical layer with optional noise.
    height_total = 2
    cube_dimension = 2
    layer_height = height_total / layers_count
    current_height = layer_index * layer_height

    # Add a cube at the specified height
    bpy.ops.mesh.primitive_cube_add(
        size=cube_dimension,
        location=(0, 0, current_height)
    )

    current_layer = bpy.context.object
    current_layer.scale[2] = layer_height / 2

    # Calculate rotation with potential noise
    rotation_angle = layer_index * angle_increment
    if randomize_rotation:
        rotation_angle += random.uniform(-max_random_offset, max_random_offset)

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
