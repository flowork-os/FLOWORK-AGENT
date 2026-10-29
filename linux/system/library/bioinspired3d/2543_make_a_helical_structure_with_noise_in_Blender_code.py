# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_helical_structure_with_noise_in_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a helical structure with noise in Blender code

import bpy
import math
import random

# Clear existing objects from the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical model
layer_amount = 9  # Number of layers
rotation_step = 20  # Degrees of rotation per layer
randomize_rotation = True  # Use noise in rotation
noise_deviation = 6  # Max noise in degrees

def build_helical_structure(layers):
    height = 2
    cube_size = 2
    layer_height = height / layers

    for index in range(layers):
        z_position = index * layer_height
        bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = layer_height / 2

        # Calculate rotation angle
        angle = index * rotation_step
        if randomize_rotation:
            angle += random.uniform(-noise_deviation, noise_deviation)

        # Rotate the layer
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(angle), orient_axis='Z')

# Create the helical structure
build_helical_structure(layer_amount)
