# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_a_helical_twisted_ply_structure_with_noise_in_each_rotation" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of a helical twisted ply structure with noise in each rotation using blender code

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
layers_count = 10  # Total layers in the helical structure
angle_per_layer = 7  # Degrees of rotation for each layer
randomize_rotation = True  # Toggle for random rotation
rotation_variation = 5  # Max deviation in degrees

def add_layer(layer_index):
    # Function to create a layer of the helix
    height = 2
    cube_size = 2
    thickness = height / layers_count
    z_position = layer_index * thickness

    # Add a cube at the calculated position
    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = thickness / 2

    # Calculate rotation with potential noise
    rotation_angle = layer_index * angle_per_layer
    if randomize_rotation:
        rotation_angle += random.uniform(-rotation_variation, rotation_variation)

    # Deselect all and select the new layer for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    # Rotate the layer around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
    return layer

# Build the helical structure
for index in range(layers_count):
    add_layer(index)
