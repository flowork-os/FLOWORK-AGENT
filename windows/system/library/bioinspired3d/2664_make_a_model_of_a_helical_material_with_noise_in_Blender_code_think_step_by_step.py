# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_a_helical_material_with_noise_in_Blender_code_think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of a helical material with noise in Blender code think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters defining the helical layers
layers_count = 10  # Total number of layers
angle_per_layer = 15  # Degrees of rotation for each layer
randomize_rotation = True  # Flag to toggle rotation noise
max_noise = 5  # Maximum noise in degrees

def generate_layer(layer_index):
    # Function to create a single helical layer with optional noise
    height_per_layer = 2 / layers_count
    z_position = layer_index * height_per_layer

    # Add a cube to represent the layer
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    current_layer = bpy.context.object
    current_layer.scale[2] = height_per_layer / 2

    # Calculate rotation with noise if enabled
    rotation_angle = layer_index * angle_per_layer
    if randomize_rotation:
        rotation_angle += random.uniform(-max_noise, max_noise)

    # Deselect all objects and select the current layer
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    # Apply rotation around Z-axis
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
    return current_layer

# Construct the helical structure
for index in range(layers_count):
    generate_layer(index)
