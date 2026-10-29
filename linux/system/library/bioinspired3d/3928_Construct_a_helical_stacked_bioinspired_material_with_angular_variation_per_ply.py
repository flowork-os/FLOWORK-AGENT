# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_helical_stacked_bioinspired_material_with_angular_variation_per_ply" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a helical stacked bioinspired material with angular variation per ply in a blender code Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical assembly
num_layers = 8  # Total layers
rotation_angle = 8  # Degrees of rotation for each layer
noise_enabled = True  # Enable noise variation
noise_strength = 7  # Maximum noise in degrees

def create_helical_structure(num_layers, rotation_angle, noise_enabled, noise_strength):
    for i in range(num_layers):
        create_layer(i, rotation_angle, noise_enabled, noise_strength)

def create_layer(index, rotation_angle, noise_enabled, noise_strength):
    height = 2
    size = 2
    layer_height = height / num_layers
    z_position = index * layer_height

    # Add a cube at the current z position
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = layer_height / 2

    # Calculate the rotation with noise
    base_rotation = index * rotation_angle
    if noise_enabled:
        base_rotation += random.uniform(-noise_strength, noise_strength)

    # Deselect all and select the current layer for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(base_rotation), orient_axis='Z')

# Invoke the structure creation
create_helical_structure(num_layers, rotation_angle, noise_enabled, noise_strength)
