# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_helical_twisted_ply_bioinspired_structure_using_python_blender_code_T" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a helical twisted ply bioinspired structure using python blender code Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_layers = 12  # Total layers in the helical structure
angle_step = 5  # Degrees of rotation for each layer

def add_helical_layer(layer_num):
    total_height = 2
    layer_size = 2
    layer_height = total_height / num_layers

    vertical_position = layer_num * layer_height

    bpy.ops.mesh.primitive_cube_add(
        size=layer_size,
        location=(0, 0, vertical_position)
    )
    current_layer = bpy.context.object
    current_layer.scale[2] = layer_height / 2

    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(layer_num * angle_step),
        orient_axis='Z'
    )

for i in range(num_layers):
    add_helical_layer(i)
