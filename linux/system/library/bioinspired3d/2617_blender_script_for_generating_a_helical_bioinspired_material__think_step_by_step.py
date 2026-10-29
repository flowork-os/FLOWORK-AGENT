# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_generating_a_helical_bioinspired_material__think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for generating a helical bioinspired material. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_layers = 12  # Number of layers in the helix
angle_step = 5  # Rotation angle for each layer

def add_layer(layer_index):
    height_total = 2  # Total height of the structure
    square_size = 2  # Size of the square layer
    layer_thickness = height_total / num_layers  # Thickness of each layer

    vertical_position = layer_index * layer_thickness

    bpy.ops.mesh.primitive_cube_add(size=square_size, location=(0, 0, vertical_position))
    current_layer = bpy.context.object
    current_layer.scale[2] = layer_thickness / 2

    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(layer_index * angle_step), orient_axis='Z')

for index in range(num_layers):
    add_layer(index)
