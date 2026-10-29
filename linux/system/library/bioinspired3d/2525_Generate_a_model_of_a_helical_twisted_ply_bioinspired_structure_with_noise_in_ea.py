# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_a_helical_twisted_ply_bioinspired_structure_with_noise_in_ea" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of a helical twisted ply bioinspired structure with noise in each rotation using Blender code

import bpy
import math
import random

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical parameters
layer_count = 9
rotation_increment = 8
introduce_noise = True
noise_variation = 7

def build_helical_cubes():
    height = 2
    width = 2
    layer_thickness = height / layer_count

    for index in range(layer_count):
        z_position = index * layer_thickness
        bpy.ops.mesh.primitive_cube_add(size=width, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = layer_thickness / 2

        # Calculate rotation with noise
        rotation_angle = index * rotation_increment
        if introduce_noise:
            rotation_angle += random.uniform(-noise_variation, noise_variation)

        # Deselect all and select the new layer
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)

        # Rotate the layer
        bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')

# Execute the creation of helical cubes
build_helical_cubes()
