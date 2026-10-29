# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_to_make_a_model_of_a_helical_Bouligand_structure_with_noise_in_ea" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code to make a model of a helical Bouligand structure with noise in each rotation think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for helical structure
layers = 12  # Number of layers
angle_step = 15  # Angle increment per layer
noise_var = 6  # Noise variation in degrees
noise_active = True  # Toggle noise

def add_helical_plate(index):
    height_total = 2
    cube_dim = 2
    thickness = height_total / layers
    z_position = index * thickness

    # Create a cube at the specified position
    bpy.ops.mesh.primitive_cube_add(size=cube_dim, location=(0, 0, z_position))
    plate = bpy.context.object
    plate.scale[2] = thickness / 2

    # Determine rotation angle
    rotation_angle = index * angle_step
    if noise_active:
        rotation_angle += random.uniform(-noise_var, noise_var)

    # Select and rotate the plate
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = plate
    plate.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')

# Construct the helical structure
for i in range(layers):
    add_helical_plate(i)
