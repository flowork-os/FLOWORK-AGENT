# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_to_construct_a_model_of_a_helical_bioinspired_structure_thin" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code to construct a model of a helical bioinspired structure think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set parameters for the helical model
layer_number = 7
rotation_increment = 20

def add_layer(index, total_layers, rotation):
    height = 2
    size = 2
    layer_thickness = height / total_layers
    z_offset = index * layer_thickness

    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_offset))
    current_layer = bpy.context.object
    current_layer.scale[2] = layer_thickness / 2
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(index * rotation), orient_axis='Z')

# Build the complete helical structure
for idx in range(layer_number):
    add_layer(idx, layer_number, rotation_increment)
