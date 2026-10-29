# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_code__construct_a_helical_stacked_structure_with_randomness_in_rot" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender code, construct a helical stacked structure with randomness in rotation. Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helix parameters
num_layers = 8  # Number of layers
rotation_angle = 10  # Rotation angle per layer

# Noise settings
is_noise_enabled = True  # Activate noise
noise_amount = 7  # Noise strength in degrees

# Helper function to create a single layer
def create_helical_layer(index):
    total_height = 2
    base_size = 2
    layer_height = total_height / num_layers
    current_z = index * layer_height

    # Create the cube
    bpy.ops.mesh.primitive_cube_add(size=base_size, location=(0, 0, current_z))
    helical_layer = bpy.context.object
    helical_layer.scale[2] = layer_height / 2

    # Determine the rotation with noise
    calculated_rotation = index * rotation_angle
    if is_noise_enabled:
        calculated_rotation += random.uniform(-noise_amount, noise_amount)

    # Rotate the layer
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = helical_layer
    helical_layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(calculated_rotation), orient_axis='Z')
    return helical_layer

# Generate the helical structure
for i in range(num_layers):
    create_helical_layer(i)
