# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_Blender_code_that_constructs_a_helical_Bouligand_bioinspired_material_w" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a Blender code that constructs a helical Bouligand bioinspired material with rotational noise

import bpy
import math
import random

# Remove all existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical structure
layers = 9  # Number of layers
rotation_angle = 8  # Degree rotation for each layer
add_noise = True  # Enable noise
noise_range = 7  # Noise range in degrees

def create_layer(idx):
    # Function to create a helical layer
    layer_height = 2.0 / layers
    z_position = idx * layer_height

    # Create a layer using a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    new_layer = bpy.context.object
    new_layer.scale[2] = layer_height / 2

    # Compute the rotation value
    total_rotation = idx * rotation_angle
    if add_noise:
        total_rotation += random.uniform(-noise_range, noise_range)

    # Select the new layer for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = new_layer
    new_layer.select_set(True)

    # Rotate the layer
    bpy.ops.transform.rotate(value=math.radians(total_rotation), orient_axis='Z')
    return new_layer

# Generate the helical structure
for i in range(layers):
    create_layer(i)
