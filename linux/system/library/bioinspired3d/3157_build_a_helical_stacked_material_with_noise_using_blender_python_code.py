# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_helical_stacked_material_with_noise_using_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a helical stacked material with noise using blender python code

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
layers_count = 10  # Number of layers in the helical structure
angle_per_layer = 15  # Angle of rotation for each layer

# Noise settings
apply_noise = True  # Toggle noise in rotation
max_noise = 5  # Maximum noise deviation in degrees

def generate_layer(layer_index):
    # Generates a single layer of the helical structure.
    height = 2
    cube_size = 2
    thickness = height / layers_count
    position_z = layer_index * thickness

    # Add a cube at the specified position
    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, position_z))
    layer_cube = bpy.context.object
    layer_cube.scale[2] = thickness / 2

    # Calculate rotation with optional noise
    rotation_angle = layer_index * angle_per_layer
    if apply_noise:
        rotation_angle += random.uniform(-max_noise, max_noise)

    # Deselect all and select the current layer for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_cube
    layer_cube.select_set(True)

    # Rotate around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
    return layer_cube

# Build the helical structure
for index in range(layers_count):
    generate_layer(index)
