# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_helical_stacked_structure_with_noise_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a helical stacked structure with noise in a blender code

import bpy
import math
import random

# Clear the scene of all objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for helical structure
layers = 15
rotation_increment = 4
enable_noise = True
max_deviation = 8

def create_helical_layers(num_layers):
    for layer_index in range(num_layers):
        create_layer(layer_index)

def create_layer(index):
    layer_height = 2 / layers
    z_position = index * layer_height

    # Add a cube to represent the layer
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    layer_object = bpy.context.object
    layer_object.scale[2] = layer_height / 2

    # Calculate the rotation
    rotation_angle = index * rotation_increment
    if enable_noise:
        rotation_angle += random.uniform(-max_deviation, max_deviation)

    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_object
    layer_object.select_set(True)

    # Rotate the layer around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')

# Create the helical layers
create_helical_layers(layers)
