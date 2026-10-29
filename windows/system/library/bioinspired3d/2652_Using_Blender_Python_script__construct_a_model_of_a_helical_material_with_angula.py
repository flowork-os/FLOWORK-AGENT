# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_Blender_Python_script__construct_a_model_of_a_helical_material_with_angula" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using Blender Python script, construct a model of a helical material with angular variation per ply Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_layers = 15  # Total layers
rotation_step = 5  # Degrees rotation per layer
noise_enabled = True  # Toggle for noise
noise_magnitude = 3  # Noise range in degrees

def generate_helical_structure(layer_count, rotation_angle, noise, noise_strength):
    for i in range(layer_count):
        height_per_layer = 2 / layer_count
        z_position = i * height_per_layer

        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
        cube = bpy.context.object
        cube.scale[2] = height_per_layer / 2

        rotation_value = i * rotation_angle
        if noise:
            rotation_value += random.uniform(-noise_strength, noise_strength)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = cube
        cube.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')

generate_helical_structure(num_layers, rotation_step, noise_enabled, noise_magnitude)
