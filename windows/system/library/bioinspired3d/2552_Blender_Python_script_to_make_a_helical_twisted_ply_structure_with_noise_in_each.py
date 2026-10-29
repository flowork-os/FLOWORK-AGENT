# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_to_make_a_helical_twisted_ply_structure_with_noise_in_each" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script to make a helical twisted ply structure with noise in each rotation

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical formation
layer_count = 8  # Total number of layers
rotation_angle = 15  # Degrees of rotation for each layer
noise_enabled = True  # Toggle noise on rotation
noise_amount = 5  # Maximum rotation noise in degrees

# Function to create individual layers
def generate_layer(layer_index):
    height_per_layer = 2 / layer_count
    layer_height = layer_index * height_per_layer

    # Add a cube at the specified height
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, layer_height))
    layer = bpy.context.object
    layer.scale[2] = height_per_layer / 2

    # Calculate rotation with potential noise
    rotation_value = layer_index * rotation_angle
    if noise_enabled:
        rotation_value += random.uniform(-noise_amount, noise_amount)

    # Deselect all and select the new layer
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    # Apply rotation around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')
    return layer

# Construct the helical structure
for index in range(layer_count):
    generate_layer(index)
