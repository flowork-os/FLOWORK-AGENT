# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_blender_python_code_that_makes_a_helical_twisted_ply_material_with_noise" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create blender python code that makes a helical twisted ply material with noise Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical structure
layers_count = 10  # Total number of layers
angle_per_layer = 7  # Degrees of rotation for each layer
noise_enabled = True  # Random noise in rotation
max_noise = 5  # Maximum noise in degrees

def generate_layer(layer_index):
    height_total = 2
    cube_size = 2
    layer_height = height_total / layers_count
    current_height = layer_index * layer_height

    # Add a cube at the specified height
    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, current_height))
    layer = bpy.context.object
    layer.scale[2] = layer_height / 2

    # Calculate the base rotation with potential noise
    rotation_angle = layer_index * angle_per_layer
    if noise_enabled:
        rotation_angle += random.uniform(-max_noise, max_noise)

    # Deselect all and select the current layer before rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    # Rotate the layer around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
    return layer

# Building the helical structure
for idx in range(layers_count):
    generate_layer(idx)
