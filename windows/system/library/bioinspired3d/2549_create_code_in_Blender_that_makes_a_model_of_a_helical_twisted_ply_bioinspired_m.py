# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_code_in_Blender_that_makes_a_model_of_a_helical_twisted_ply_bioinspired_m" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create code in Blender that makes a model of a helical twisted ply bioinspired material with noise in each rotation.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical formation
layers_count = 10  # Total number of layers
angle_per_layer = 15  # Degrees of rotation for each layer
noise_enabled = True  # Toggle for noise in rotation
max_noise = 5  # Maximum noise in degrees

def generate_layer(index):
    layer_height = 2
    layer_size = 2
    thickness = layer_height / layers_count
    z_position = index * thickness

    # Add cube mesh
    bpy.ops.mesh.primitive_cube_add(size=layer_size, location=(0, 0, z_position))
    current_layer = bpy.context.object
    current_layer.scale[2] = thickness / 2

    # Calculate rotation with noise
    rotation_angle = index * angle_per_layer
    if noise_enabled:
        rotation_angle += random.uniform(-max_noise, max_noise)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    # Rotate the layer
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
    return current_layer

# Build the helical structure
for i in range(layers_count):
    generate_layer(i)
