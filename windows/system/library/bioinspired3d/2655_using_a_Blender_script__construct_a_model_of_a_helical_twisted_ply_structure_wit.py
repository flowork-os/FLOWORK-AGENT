# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_script__construct_a_model_of_a_helical_twisted_ply_structure_wit" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender script, construct a model of a helical twisted ply structure with noise. think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical model
layers_count = 10  # Total layers in the structure
angle_per_layer = 15  # Degrees of rotation for each layer

# Randomness settings for rotation
apply_randomness = True  # Toggle rotation randomness
random_deviation = 5  # Max deviation in degrees

def generate_layer(layer_index):
    # Function to create a single layer of the helical structure.

    height_total = 2
    cube_size = 2
    layer_thickness = height_total / layers_count
    current_height = layer_index * layer_thickness

    # Add a cube at the specified height
    bpy.ops.mesh.primitive_cube_add(
        size=cube_size,
        location=(0, 0, current_height)
    )

    cube = bpy.context.object
    cube.scale[2] = layer_thickness / 2

    # Calculate base rotation with potential noise
    rotation_angle = layer_index * angle_per_layer
    if apply_randomness:
        rotation_angle += random.uniform(-random_deviation, random_deviation)

    # Deselect all and select the new cube for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = cube
    cube.select_set(True)

    # Rotate the cube around the Z-axis
    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )
    return cube

# Build the helical structure
for index in range(layers_count):
    generate_layer(index)
