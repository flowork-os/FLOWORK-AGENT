# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_a_helical_twisted_ply_bioinspired_structure_with_randomness_in" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of a helical twisted ply bioinspired structure with randomness in rotation in blender script think step by step.

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
    overall_height = 2
    cube_dim = 2
    layer_height = overall_height / number_of_layers
    position_z = index * layer_height

    bpy.ops.mesh.primitive_cube_add(
        size=cube_dim,
        location=(0, 0, position_z)
    )
    helical_cube = bpy.context.object
    helical_cube.scale[2] = layer_height / 2

    rotation_angle = index * angle_increment
    if enable_noise:
        rotation_angle += random.uniform(-noise_range, noise_range)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = helical_cube
    helical_cube.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

for i in range(number_of_layers):
    make_helical_layer(i)
