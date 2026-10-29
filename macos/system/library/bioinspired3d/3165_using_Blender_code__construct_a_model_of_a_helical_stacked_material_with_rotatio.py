# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_code__construct_a_model_of_a_helical_stacked_material_with_rotatio" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender code, construct a model of a helical stacked material with rotational noise

import bpy
import math
import random

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Settings for the helical design
total_layers = 6  # Number of layers in the helical form
layer_rotation = 18  # Rotation in degrees for each layer
apply_noise = True  # Flag for noise application
noise_limit = 7  # Noise limit in degrees

def create_helical_layers(num_layers, rotation_step, noise_flag, noise_limit):
    for i in range(num_layers):
        height_per_layer = 2 / num_layers
        z_position = i * height_per_layer

        # Add a cube at the current position
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
        cube = bpy.context.object
        cube.scale[2] = height_per_layer / 2

        # Calculate the rotation with noise
        rotation_value = i * rotation_step
        if noise_flag:
            rotation_value += random.uniform(-noise_limit, noise_limit)

        # Select and rotate the cube
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = cube
        cube.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')

# Generate the helical structure
create_helical_layers(total_layers, layer_rotation, apply_noise, noise_limit)
