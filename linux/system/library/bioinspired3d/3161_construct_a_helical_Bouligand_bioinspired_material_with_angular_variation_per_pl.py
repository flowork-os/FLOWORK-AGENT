# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_helical_Bouligand_bioinspired_material_with_angular_variation_per_pl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a helical Bouligand bioinspired material with angular variation per ply in blender code

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure settings
total_layers = 6  # Number of layers in the helix
angle_increment = 8  # Degrees of rotation for each layer

# Noise settings
add_noise = True  # Whether to add noise to the rotation
noise_range = 9  # Maximum noise in degrees

def create_layer(index):
    # Creates a single layer of the helical structure with optional noise.
    height = 2
    cube_size = 2
    layer_height = height / total_layers
    z_position = index * layer_height

    # Create a cube at the specified position
    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
    layer_cube = bpy.context.object
    layer_cube.scale[2] = layer_height / 2

    # Calculate rotation angle with optional noise
    rotation_angle = index * angle_increment
    if add_noise:
        rotation_angle += random.uniform(-noise_range, noise_range)

    # Deselect all and select the current layer for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_cube
    layer_cube.select_set(True)

    # Rotate around Z-axis
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
    return layer_cube

# Construct the helical structure
for i in range(total_layers):
    create_layer(i)
