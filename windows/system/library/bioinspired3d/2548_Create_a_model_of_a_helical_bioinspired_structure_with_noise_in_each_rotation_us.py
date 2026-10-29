# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_a_helical_bioinspired_structure_with_noise_in_each_rotation_us" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of a helical bioinspired structure with noise in each rotation using blender code

import bpy
import math
import random

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical structure
layer_number = 14
rotation_step = 8
add_noise = True
noise_range = 7

# Function to generate the helical structure
def generate_layers():
    for index in range(layer_number):
        create_layer(index)

def create_layer(index):
    height = 2
    size = 2
    layer_thickness = height / layer_number
    z_position = index * layer_thickness

    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = layer_thickness / 2

    current_rotation = index * rotation_step
    if add_noise:
        current_rotation += random.uniform(-noise_range, noise_range)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(current_rotation), orient_axis='Z')

# Execute layer generation
generate_layers()
