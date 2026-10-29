# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_code_that_makes_a_helical_twisted_ply_material_with_rotational" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender code that makes a helical twisted ply material with rotational noise

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical structure
layers_count = 10  # Total number of layers
angle_increment = 5  # Degrees of rotation per layer
noise_enabled = True  # Toggle noise in rotation
max_noise = 5  # Max noise in degrees

def generate_layer(layer_index):
    height = 2
    width = 2
    layer_height = height / layers_count
    z_position = layer_index * layer_height

    # Add a cube at the calculated position
    bpy.ops.mesh.primitive_cube_add(size=width, location=(0, 0, z_position))
    current_layer = bpy.context.object
    current_layer.scale[2] = layer_height / 2

    # Calculate rotation with optional noise
    rotation_angle = layer_index * angle_increment
    if noise_enabled:
        rotation_angle += random.uniform(-max_noise, max_noise)

    # Deselect all and prepare to rotate the new layer
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    # Apply rotation around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
    return current_layer

# Build the helical structure
for idx in range(layers_count):
    generate_layer(idx)
