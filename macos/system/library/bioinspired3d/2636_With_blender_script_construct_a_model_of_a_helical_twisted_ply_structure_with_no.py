# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_script_construct_a_model_of_a_helical_twisted_ply_structure_with_no" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender script construct a model of a helical twisted ply structure with noise in each rotation. think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_layers = 12
rotation_increment = 5
random_rotation = True
rotation_noise = 4

def add_helical_layer(layer_index):
    height_per_layer = 2 / num_layers
    z_offset = layer_index * height_per_layer

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_offset))
    current_layer = bpy.context.object
    current_layer.scale[2] = height_per_layer / 2

    rotation_angle = layer_index * rotation_increment
    if random_rotation:
        rotation_angle += random.uniform(-rotation_noise, rotation_noise)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')

for i in range(num_layers):
    add_helical_layer(i)
