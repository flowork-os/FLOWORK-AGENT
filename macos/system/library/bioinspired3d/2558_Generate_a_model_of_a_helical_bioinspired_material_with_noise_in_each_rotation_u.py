# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_a_helical_bioinspired_material_with_noise_in_each_rotation_u" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of a helical bioinspired material with noise in each rotation using code in Blender

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure settings
number_of_layers = 6  # Total layers
angle_increment = 12  # Degrees rotation for each layer

# Noise settings
enable_noise = True  # Turn on rotation noise?
noise_range = 6  # Max noise in degrees

def make_helical_layer(index):
    # Function to create a single helical layer.

    overall_height = 2
    cube_dim = 2
    layer_height = overall_height / number_of_layers
    position_z = index * layer_height

    # Create a cube at the specified height
    bpy.ops.mesh.primitive_cube_add(
        size=cube_dim,
        location=(0, 0, position_z)
    )

    helical_cube = bpy.context.object
    helical_cube.scale[2] = layer_height / 2

    # Calculate rotation angle
    rotation_angle = index * angle_increment
    if enable_noise:
        rotation_angle += random.uniform(-noise_range, noise_range)

    # Deselect all objects and select the new cube for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = helical_cube
    helical_cube.select_set(True)

    # Rotate the cube around the Z-axis
    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

# Generate the helical structure
for i in range(number_of_layers):
    make_helical_layer(i)
