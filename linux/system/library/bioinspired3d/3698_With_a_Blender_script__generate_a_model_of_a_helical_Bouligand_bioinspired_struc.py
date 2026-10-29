# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_script__generate_a_model_of_a_helical_Bouligand_bioinspired_struc" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender script, generate a model of a helical Bouligand bioinspired structure. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_layers = 9  # Total number of layers
rotation_degrees = 20  # Rotation for each layer

def add_layer(index):
    height = 2  # Complete height of the structure
    size = 2  # Dimension of each square layer
    layer_height = height / num_layers  # Height of each layer

    z_position = index * layer_height
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = layer_height / 2

    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(index * rotation_degrees), orient_axis='Z')

for i in range(num_layers):
    add_layer(i)
