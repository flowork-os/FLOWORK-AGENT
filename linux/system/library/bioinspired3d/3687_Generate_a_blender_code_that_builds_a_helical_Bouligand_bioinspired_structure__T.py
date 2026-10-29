# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_blender_code_that_builds_a_helical_Bouligand_bioinspired_structure__T" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a blender code that builds a helical Bouligand bioinspired structure. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for helical design
layers = 6  # Number of layers in the design
angle_per_layer = 18  # Degree of rotation for each layer

def add_layer(index):
    height_of_model = 2
    cube_size = 2
    layer_height = height_of_model / layers
    z_offset = index * layer_height

    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_offset))
    layer = bpy.context.object
    layer.scale[2] = layer_height / 2
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(index * angle_per_layer), orient_axis='Z')

# Construct the helical model
for idx in range(layers):
    add_layer(idx)
