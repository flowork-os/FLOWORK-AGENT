# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_script_that_constructs_a_model_of_a_helical_stacked_bioinspired" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender script that constructs a model of a helical stacked bioinspired structure with rotational noise.

import bpy
import math
import random

# Clear the scene before creating new objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
layer_count = 15  # Number of layers
rotation_angle = 8  # Rotation angle in degrees
noise_enabled = True  # Enable random noise
noise_strength = 3  # Noise deviation

def add_layer(index):
    height = 2
    cube_size = 2
    layer_thickness = height / layer_count
    z_position = index * layer_thickness

    # Add a cube for the layer
    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
    current_layer = bpy.context.object
    current_layer.scale[2] = layer_thickness / 2

    # Calculate rotation
    rotation_value = index * rotation_angle
    if noise_enabled:
        rotation_value += random.uniform(-noise_strength, noise_strength)

    # Rotate the current layer
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')

# Create the helical structure
for layer_index in range(layer_count):
    add_layer(layer_index)
