# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_code_in_Blender__build_a_helical_stacked_bioinspired_structure_with_random" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using code in Blender, build a helical stacked bioinspired structure with randomness in rotation.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for helical structure
layers = 10  # Number of layers in the structure
angle_per_layer = 15  # Rotation angle in degrees for each layer
noise_enabled = True  # Toggle noise in rotation
max_noise = 5  # Max deviation from base rotation

def add_layer(layer_index):
    height = 2
    size = 2
    thickness = height / layers
    z_position = layer_index * thickness

    # Add a cube at the calculated position
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = thickness / 2

    # Calculate rotation with noise
    rotation = layer_index * angle_per_layer
    if noise_enabled:
        rotation += random.uniform(-max_noise, max_noise)

    # Deselect all objects and select the current layer
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    # Apply rotation to the layer
    bpy.ops.transform.rotate(value=math.radians(rotation), orient_axis='Z')
    return layer

# Build the helical structure
for index in range(layers):
    add_layer(index)
