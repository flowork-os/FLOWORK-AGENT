# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_code__build_a_model_of_a_helical_bioinspired_structure_with_rot" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender code, build a model of a helical bioinspired structure with rotational noise

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
layers_count = 10  # Total layers in the structure
angle_increment = 5  # Degrees of rotation for each layer
noise_enabled = True  # Toggle for noise
max_noise = 4  # Maximum noise in degrees

def generate_layer(layer_index):
    # Constructs a helical layer with optional noise.
    total_height = 2
    cube_size = 2
    layer_height = total_height / layers_count
    z_position = layer_index * layer_height

    # Add a cube at specified position
    bpy.ops.mesh.primitive_cube_add(
        size=cube_size,
        location=(0, 0, z_position)
    )

    current_layer = bpy.context.object
    current_layer.scale[2] = layer_height / 2

    # Calculate base rotation and add noise if enabled
    rotation_angle = layer_index * angle_increment
    if noise_enabled:
        rotation_angle += random.uniform(-max_noise, max_noise)

    # Deselect all objects, then select the current layer for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    # Apply rotation around Z-axis
    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )
    return current_layer

# Build the helical structure
for index in range(layers_count):
    generate_layer(index)
