# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_blender_script__generate_a_model_of_a_helical_Bouligand_material_with_a" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using blender script, generate a model of a helical Bouligand material with angular variation per ply think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for helical structure
num_layers = 12
rotation_increment = 20
noise_enabled = True
noise_variation = 7

def add_layer(layer_idx):
    height = 2
    size = 2
    thickness = height / num_layers
    z_position = layer_idx * thickness

    # Create a cube mesh
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = thickness / 2

    # Calculate rotation with potential noise
    angle = layer_idx * rotation_increment
    if noise_enabled:
        angle += random.uniform(-noise_variation, noise_variation)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    # Rotate the object around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(angle), orient_axis='Z')
    return layer

# Construct the helical structure
for i in range(num_layers):
    add_layer(i)
