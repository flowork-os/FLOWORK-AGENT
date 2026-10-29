# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_code_that_generates_a_helical_stacked_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender code that generates a helical stacked bioinspired structure

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical assembly
layer_count = 9  # Number of layers in the assembly
rotation_increment = 5  # Incremental rotation in degrees

# Function to build a helical layer
def build_helical_layer(layer_num):
    overall_height = 2
    plate_length = 2
    layer_height = overall_height / layer_count
    z_coordinate = layer_num * layer_height

    bpy.ops.mesh.primitive_cube_add(size=plate_length, location=(0, 0, z_coordinate))
    layer = bpy.context.object
    layer.scale[2] = layer_height / 2
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(layer_num * rotation_increment), orient_axis='Z')

# Generate the helical layers
for num in range(layer_count):
    build_helical_layer(num)
