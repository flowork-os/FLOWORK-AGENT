# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_helical_bioinspired_material_with_noise_in_each_rotation_using_code_i" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a helical bioinspired material with noise in each rotation using code in Blender

import bpy
import math
import random

# Remove all objects from the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the helical structure's parameters
num_layers = 12
angle_increment = 15
enable_noise = True
max_noise = 6

def generate_helical_structure(num_layers, angle_increment, enable_noise, max_noise):
    for i in range(num_layers):
        create_helical_layer(i, angle_increment, enable_noise, max_noise)

def create_helical_layer(index, angle_increment, enable_noise, max_noise):
    height = 2
    cube_size = 2
    layer_thickness = height / num_layers
    z_position = index * layer_thickness

    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = layer_thickness / 2

    base_angle = index * angle_increment
    if enable_noise:
        base_angle += random.uniform(-max_noise, max_noise)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(base_angle), orient_axis='Z')

# Generate the helical structure
generate_helical_structure(num_layers, angle_increment, enable_noise, max_noise)
