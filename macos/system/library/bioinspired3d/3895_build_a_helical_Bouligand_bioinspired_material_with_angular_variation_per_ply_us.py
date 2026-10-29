# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_helical_Bouligand_bioinspired_material_with_angular_variation_per_ply_us" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a helical Bouligand bioinspired material with angular variation per ply using blender code Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical structure
layers_count = 10  # Total number of layers
rotation_angle = 15  # Degrees of rotation per layer
noise_enabled = True  # Toggle noise in rotation
max_noise = 5  # Maximum noise deviation in degrees

# Function to generate a single layer of the helical structure
def generate_layer(layer_index):
    height = 2
    size = 2
    thickness = height / layers_count
    current_height = layer_index * thickness

    # Add a cube to the scene
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, current_height))
    current_layer = bpy.context.object
    current_layer.scale[2] = thickness / 2

    # Calculate rotation with noise
    rotation_value = layer_index * rotation_angle
    if noise_enabled:
        rotation_value += random.uniform(-max_noise, max_noise)

    # Deselect all and select the current layer for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    # Rotate the layer
    bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')
    return current_layer

# Build the helical structure
for index in range(layers_count):
    generate_layer(index)
