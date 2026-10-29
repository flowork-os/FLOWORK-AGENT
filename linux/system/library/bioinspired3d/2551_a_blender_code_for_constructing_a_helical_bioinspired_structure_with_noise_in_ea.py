# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_for_constructing_a_helical_bioinspired_structure_with_noise_in_ea" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code for constructing a helical bioinspired structure with noise in each rotation.

import bpy
import math
import random

# Scene cleanup
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure settings
layer_num = 15
rotation_angle = 3
is_noise_enabled = True
noise_strength = 6

def create_helical_structure(index):
    height_total = 2
    cube_size = 2
    layer_thickness = height_total / layer_num
    z_coordinate = index * layer_thickness

    # Add cube to scene
    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_coordinate))
    helical_layer = bpy.context.object
    helical_layer.scale[2] = layer_thickness / 2

    # Calculate rotation with noise
    base_rotation = index * rotation_angle
    if is_noise_enabled:
        base_rotation += random.uniform(-noise_strength, noise_strength)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = helical_layer
    helical_layer.select_set(True)

    # Apply rotation
    bpy.ops.transform.rotate(value=math.radians(base_rotation), orient_axis='Z')
    return helical_layer

# Generate each helical layer
for i in range(layer_num):
    create_helical_structure(i)
