# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_creates_a_model_of_a_helical_stacked_bioinspired_mate" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that creates a model of a helical stacked bioinspired material with angular variation per ply

import bpy
import math
import random

# Clear all objects in the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical model
layers = 6  # Number of layers
ply_rotation = 8  # Degrees of rotation for each layer

# Noise settings for randomness
is_noise_active = True  # Activate noise
noise_limit = 3  # Max noise in degrees

def make_helical_layers(num_layers):
    layer_height = 2 / num_layers
    for idx in range(num_layers):
        z_coord = idx * layer_height

        # Add a cube as a plate
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_coord))
        layer = bpy.context.object
        layer.scale[2] = layer_height / 2

        # Determine rotation angle
        rotation_angle = idx * ply_rotation
        if is_noise_active:
            rotation_angle += random.uniform(-noise_limit, noise_limit)

        # Rotate the layer
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')

# Create the helical structure
make_helical_layers(layers)
