# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_Blender_Python_script_that_builds_a_helical_twisted_ply_bioinspired_materi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write Blender Python script that builds a helical twisted ply bioinspired material with rotational noise. think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helix parameters
layer_count = 6
angle_increment = 5
apply_noise = True
noise_range = 8

def build_layer(index):
    total_height = 2
    cube_size = 2
    layer_height = total_height / layer_count
    z_offset = index * layer_height

    # Generate a cube
    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_offset))
    new_layer = bpy.context.object
    new_layer.scale[2] = layer_height / 2

    # Compute rotation angle with noise
    rotation_angle = index * angle_increment
    if apply_noise:
        rotation_angle += random.uniform(-noise_range, noise_range)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = new_layer
    new_layer.select_set(True)

    # Rotate the layer
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
    return new_layer

# Create the helical structure
for idx in range(layer_count):
    build_layer(idx)
