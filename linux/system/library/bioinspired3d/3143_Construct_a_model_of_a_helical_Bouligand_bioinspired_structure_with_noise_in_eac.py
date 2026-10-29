# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_a_helical_Bouligand_bioinspired_structure_with_noise_in_eac" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of a helical Bouligand bioinspired structure with noise in each rotation in a Blender code

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
num_layers = 12
rotation_angle = 15
noise_enabled = True
max_deviation = 5

def add_helical_layer(index):
    height_of_stack = 2
    cube_dimension = 2
    layer_height = height_of_stack / num_layers
    z_position = index * layer_height

    bpy.ops.mesh.primitive_cube_add(
        size=cube_dimension,
        location=(0, 0, z_position)
    )

    layer = bpy.context.object
    layer.scale[2] = layer_height / 2

    base_rotation = index * rotation_angle
    if noise_enabled:
        base_rotation += random.uniform(-max_deviation, max_deviation)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(base_rotation),
        orient_axis='Z'
    )

for i in range(num_layers):
    add_helical_layer(i)
