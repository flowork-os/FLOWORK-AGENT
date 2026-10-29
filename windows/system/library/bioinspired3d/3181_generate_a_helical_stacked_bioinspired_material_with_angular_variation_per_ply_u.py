# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_helical_stacked_bioinspired_material_with_angular_variation_per_ply_u" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a helical stacked bioinspired material with angular variation per ply using code in Blender

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
layers_count = 10  # Total number of layers
rotation_angle = 5  # Degrees of rotation per layer
noise_enabled = True  # Toggle for noise effect
max_noise = 5  # Maximum noise in degrees

def generate_layer(layer_index):
    height = 2
    size = 2
    thickness = height / layers_count
    z_position = layer_index * thickness

    # Add a cube mesh at the calculated position
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = thickness / 2

    # Calculate rotation with potential noise
    rotation_value = layer_index * rotation_angle
    if noise_enabled:
        rotation_value += random.uniform(-max_noise, max_noise)

    # Deselect all and select the current layer for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    # Rotate the layer around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')
    return layer

# Build the helical structure
for index in range(layers_count):
    generate_layer(index)
