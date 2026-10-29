# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_to_create_a_model_of_a_helical_material_with_randomness_in_rotation" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code to create a model of a helical material with randomness in rotation.

import bpy
import math
import random

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helix parameters
num_layers = 12
layer_rotation = 8
noise_enabled = True
noise_intensity = 6

def add_helical_layer(idx):
    z_offset = 2 * idx / num_layers
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_offset))
    current_layer = bpy.context.object
    current_layer.scale[2] = 1 / num_layers

    rotation = idx * layer_rotation
    if noise_enabled:
        rotation += random.uniform(-noise_intensity, noise_intensity)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(rotation), orient_axis='Z')

# Generate the helical structure
for i in range(num_layers):
    add_helical_layer(i)
