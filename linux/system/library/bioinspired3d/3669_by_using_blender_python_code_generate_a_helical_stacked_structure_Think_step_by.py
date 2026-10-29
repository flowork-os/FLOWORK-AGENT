# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_blender_python_code_generate_a_helical_stacked_structure_Think_step_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using blender python code generate a helical stacked structure Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helix
layers_count = 10  # Total number of layers
angle_per_layer = 15  # Degrees of rotation per layer

def generate_layer(layer_index):
    height_of_structure = 2  # Complete height
    plate_dimension = 2  # Dimensions of the square plate
    thickness_of_layer = height_of_structure / layers_count  # Layer thickness

    z_position = layer_index * thickness_of_layer  # Compute vertical position

    bpy.ops.mesh.primitive_cube_add(size=plate_dimension, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = thickness_of_layer / 2  # Scale to thin plate

    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(layer_index * angle_per_layer), orient_axis='Z')

    return layer

# Create the helix
for index in range(layers_count):
    generate_layer(index)
