# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_script__generate_a_model_of_a_helical_twisted_ply_bioinspired_mater" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender script, generate a model of a helical twisted ply bioinspired material with noise think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
layers_count = 10  # Total number of layers
angle_increment = 5  # Degrees of rotation per layer
noise_enabled = True  # Whether to apply random noise
deviation_strength = 4  # Max noise in degrees

def generate_layer(layer_index):
    # Constructs a layer of the helical structure
    height = 2
    cube_size = 2
    layer_height = height / layers_count
    z_position = layer_index * layer_height

    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = layer_height / 2

    # Calculate rotation with possible noise
    rotation_angle = layer_index * angle_increment
    if noise_enabled:
        rotation_angle += random.uniform(-deviation_strength, deviation_strength)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
    return layer

# Build the helical structure
for index in range(layers_count):
    generate_layer(index)
