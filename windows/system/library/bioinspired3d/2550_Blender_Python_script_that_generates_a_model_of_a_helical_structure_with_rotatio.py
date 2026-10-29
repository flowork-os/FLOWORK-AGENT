# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_generates_a_model_of_a_helical_structure_with_rotatio" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that generates a model of a helical structure with rotational noise.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure configuration
ply_count = 8
rotation_step = 10
noise_active = True
noise_amount = 4

def create_helical_layer(layer_index):
    height_total = 2
    cube_dimension = 2
    layer_thickness = height_total / ply_count
    z_coordinate = layer_index * layer_thickness

    # Insert cube at calculated position
    bpy.ops.mesh.primitive_cube_add(size=cube_dimension, location=(0, 0, z_coordinate))
    layer_object = bpy.context.object
    layer_object.scale[2] = layer_thickness / 2

    # Determine rotation with possible noise
    rotation_angle = layer_index * rotation_step
    if noise_active:
        rotation_angle += random.uniform(-noise_amount, noise_amount)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_object
    layer_object.select_set(True)

    # Apply rotation
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
    return layer_object

# Generate the helical form
for index in range(0, ply_count):
    create_helical_layer(index)
