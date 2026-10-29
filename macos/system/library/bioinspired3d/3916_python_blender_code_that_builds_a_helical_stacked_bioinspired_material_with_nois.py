# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_that_builds_a_helical_stacked_bioinspired_material_with_nois" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code that builds a helical stacked bioinspired material with noise think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure configuration
num_layers = 8  # Number of layers in the helical structure
layer_rotation = 10  # Each layer rotates by this angle

# Noise configuration
add_noise = True  # Should we add noise?
noise_amplitude = 4  # Maximum noise in degrees

def create_helical_layer(layer_num):
    # Creates a helical layer with optional noise in rotation.

    total_height = 2
    cube_dimension = 2
    thickness_per_layer = total_height / num_layers
    current_z = layer_num * thickness_per_layer

    # Add a cube at the layer's height
    bpy.ops.mesh.primitive_cube_add(
        size=cube_dimension,
        location=(0, 0, current_z)
    )

    layer_cube = bpy.context.object
    layer_cube.scale[2] = thickness_per_layer / 2

    # Calculate base rotation with noise
    rotation_value = layer_num * layer_rotation
    if add_noise:
        rotation_value += random.uniform(-noise_amplitude, noise_amplitude)

    # Select the new cube for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_cube
    layer_cube.select_set(True)

    # Rotate around the Z-axis
    bpy.ops.transform.rotate(
        value=math.radians(rotation_value),
        orient_axis='Z'
    )
    return layer_cube

# Generate the entire helical structure
for i in range(num_layers):
    create_helical_layer(i)
