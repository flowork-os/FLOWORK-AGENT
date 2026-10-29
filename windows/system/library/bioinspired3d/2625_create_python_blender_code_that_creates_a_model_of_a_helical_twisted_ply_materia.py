# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_python_blender_code_that_creates_a_model_of_a_helical_twisted_ply_materia" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create python blender code that creates a model of a helical twisted ply material with randomness in rotation. Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_layers = 12
angle_increment = 5
is_noise_enabled = True
noise_variation = 6

def create_helical_structure(num_layers):
    for i in range(num_layers):
        create_single_layer(i)

def create_single_layer(index):
    height = 2
    cube_size = 2
    layer_thickness = height / num_layers
    z_offset = index * layer_thickness

    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_offset))
    layer = bpy.context.object
    layer.scale[2] = layer_thickness / 2

    rotation_angle = index * angle_increment
    if is_noise_enabled:
        rotation_angle += random.uniform(-noise_variation, noise_variation)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')

create_helical_structure(num_layers)
