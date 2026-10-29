# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_a_helical_twisted_ply_structure_with_noise_in_each_rotation_usi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of a helical twisted ply structure with noise in each rotation using a blender code think step by step

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
