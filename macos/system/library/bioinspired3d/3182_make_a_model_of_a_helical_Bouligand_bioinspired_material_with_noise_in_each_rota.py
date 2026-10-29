# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_a_helical_Bouligand_bioinspired_material_with_noise_in_each_rota" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of a helical Bouligand bioinspired material with noise in each rotation in Blender Python script

import bpy
import math
import random

# Remove all objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for helical structure
layer_count = 9
rotation_step = 10
randomize_rotation = True
rotation_variation = 7

def create_cuboid(index):
    height = 2
    base_size = 2
    layer_height = height / layer_count
    z_position = index * layer_height

    bpy.ops.mesh.primitive_cube_add(size=base_size, location=(0, 0, z_position))
    cuboid = bpy.context.object
    cuboid.scale[2] = layer_height / 2

    rotation_value = index * rotation_step
    if randomize_rotation:
        rotation_value += random.uniform(-rotation_variation, rotation_variation)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = cuboid
    cuboid.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')

# Construct the helical structure
for i in range(layer_count):
    create_cuboid(i)
