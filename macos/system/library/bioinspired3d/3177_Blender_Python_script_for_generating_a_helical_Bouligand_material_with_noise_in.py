# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_for_generating_a_helical_Bouligand_material_with_noise_in" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script for generating a helical Bouligand material with noise in each rotation

import bpy
import math
import random

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
ply_count = 8
angle_increment = 10
noise_enabled = True
noise_variation = 6

def generate_helix(ply_count, angle_increment, noise_enabled, noise_variation):
    for i in range(ply_count):
        create_helix_layer(i, angle_increment, noise_enabled, noise_variation)

def create_helix_layer(index, angle_increment, noise_enabled, noise_variation):
    height = 2
    cube_size = 2
    layer_thickness = height / ply_count
    z_position = index * layer_thickness

    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
    current_layer = bpy.context.object
    current_layer.scale[2] = layer_thickness / 2

    rotation_angle = index * angle_increment
    if noise_enabled:
        rotation_angle += random.uniform(-noise_variation, noise_variation)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')

# Execute the helix generation
generate_helix(ply_count, angle_increment, noise_enabled, noise_variation)
