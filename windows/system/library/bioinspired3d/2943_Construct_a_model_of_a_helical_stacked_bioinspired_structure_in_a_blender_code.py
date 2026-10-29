# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_a_helical_stacked_bioinspired_structure_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of a helical stacked bioinspired structure in a blender code

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure configuration
layer_amount = 9
angle_per_layer = 12

def construct_helical_layer(layer_index):
    overall_height = 2
    cube_size = 2
    layer_depth = overall_height / layer_amount

    z_coord = layer_index * layer_depth
    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_coord))
    layer = bpy.context.object
    layer.scale[2] = layer_depth / 2

    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(layer_index * angle_per_layer), orient_axis='Z')

for index in range(layer_amount):
    construct_helical_layer(index)
