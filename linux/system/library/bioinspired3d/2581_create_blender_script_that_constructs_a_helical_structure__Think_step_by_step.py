# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_blender_script_that_constructs_a_helical_structure__Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create blender script that constructs a helical structure. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical model
num_layers = 12
angle_step = 10

def add_layer(layer_num):
    total_height = 2
    cube_size = 2
    layer_height = total_height / num_layers

    z_coord = layer_num * layer_height
    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_coord))
    layer_object = bpy.context.object
    layer_object.scale[2] = layer_height / 2

    bpy.context.view_layer.objects.active = layer_object
    layer_object.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(layer_num * angle_step), orient_axis='Z')

# Construct the helical structure
for layer in range(num_layers):
    add_layer(layer)
