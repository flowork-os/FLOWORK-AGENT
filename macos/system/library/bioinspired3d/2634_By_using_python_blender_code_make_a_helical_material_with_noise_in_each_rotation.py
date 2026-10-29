# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_python_blender_code_make_a_helical_material_with_noise_in_each_rotation" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using python blender code make a helical material with noise in each rotation. think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_total = 9  # Number of layers
rotation_increment = 12  # Rotation increment per layer
noise_enabled = True  # Use noise for rotation
max_rotation_noise = 8  # Max noise amount

def create_helical_structure(total_layers, rotation_step, noise, max_noise):
    for i in range(total_layers):
        height = 2
        layer_size = 2
        layer_thickness = height / total_layers
        z_position = i * layer_thickness

        bpy.ops.mesh.primitive_cube_add(size=layer_size, location=(0, 0, z_position))
        layer_object = bpy.context.object
        layer_object.scale[2] = layer_thickness / 2

        rotation_value = i * rotation_step
        if noise:
            rotation_value += random.uniform(-max_noise, max_noise)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer_object
        layer_object.select_set(True)

        bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')

create_helical_structure(layer_total, rotation_increment, noise_enabled, max_rotation_noise)
