# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_code_make_a_model_of_a_helical_material_with_noise_Think_step_by_s" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender code make a model of a helical material with noise Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for creating a helical layer structure
layers_count = 10  # Total number of layers
angle_per_layer = 7  # Degrees of rotation for each layer
randomize_rotation = True  # Toggle for random rotation
max_noise = 5  # Maximum rotation deviation

def generate_layer(layer_index):
    # Function to generate a single layer of the helical structure.
    height_of_layer = 2
    cube_dimension = 2
    thickness_of_layer = height_of_layer / layers_count
    z_position = layer_index * thickness_of_layer

    # Add a cube mesh at the specified location
    bpy.ops.mesh.primitive_cube_add(size=cube_dimension, location=(0, 0, z_position))
    current_layer = bpy.context.object
    current_layer.scale[2] = thickness_of_layer / 2

    # Calculate rotation with potential noise
    rotation_angle = layer_index * angle_per_layer
    if randomize_rotation:
        rotation_angle += random.uniform(-max_noise, max_noise)

    # Deselect all and select the current layer for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    # Apply rotation about the Z-axis
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
    return current_layer

# Create the helical structure
for idx in range(layers_count):
    generate_layer(idx)
