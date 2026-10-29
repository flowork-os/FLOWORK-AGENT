# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_helical_Bouligand_structure_with_angular_variation_per_ply_in_blender_sc" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a helical Bouligand structure with angular variation per ply in blender script

import bpy
import math
import random

# Clear existing objects in the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical structure parameters
num_layers = 7  # Number of layers in the helical structure
rotation_angle = 10  # Angle of rotation for each layer
noise_enabled = True  # Toggle for noise in rotation
noise_amount = 4  # Maximum rotation noise

def create_helical_layer(index):
    # Create a single layer of the helical structure
    layer_height = 2.0 / num_layers
    z_position = index * layer_height

    # Add a cube to represent the layer
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = layer_height / 2

    # Calculate the rotation angle
    angle = index * rotation_angle
    if noise_enabled:
        angle += random.uniform(-noise_amount, noise_amount)

    # Deselect all and select the current layer
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    # Rotate the layer
    bpy.ops.transform.rotate(value=math.radians(angle), orient_axis='Z')
    return layer

# Generate the entire helical structure
for i in range(num_layers):
    create_helical_layer(i)
