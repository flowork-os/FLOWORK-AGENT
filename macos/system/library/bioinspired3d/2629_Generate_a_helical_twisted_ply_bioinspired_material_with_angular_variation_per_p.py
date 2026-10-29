# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_helical_twisted_ply_bioinspired_material_with_angular_variation_per_p" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a helical twisted ply bioinspired material with angular variation per ply in a blender code think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical structure
layer_count = 7
increment_angle = 12
randomize_rotation = True
rotation_variation = 3

def create_helical_geometry(layer_index):
    total_height = 2
    cube_size = 2
    height_per_layer = total_height / layer_count
    z_coord = layer_index * height_per_layer

    bpy.ops.mesh.primitive_cube_add(
        size=cube_size,
        location=(0, 0, z_coord)
    )

    layer_object = bpy.context.object
    layer_object.scale[2] = height_per_layer / 2

    base_angle = layer_index * increment_angle
    if randomize_rotation:
        base_angle += random.uniform(-rotation_variation, rotation_variation)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_object
    layer_object.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(base_angle),
        orient_axis='Z'
    )

for index in range(layer_count):
    create_helical_geometry(index)
