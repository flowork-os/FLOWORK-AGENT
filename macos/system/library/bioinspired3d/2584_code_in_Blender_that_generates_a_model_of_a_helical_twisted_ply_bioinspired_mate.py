# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_that_generates_a_model_of_a_helical_twisted_ply_bioinspired_mate" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender that generates a model of a helical twisted ply bioinspired material. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical assembly
layers_count = 10  # Total layers in the structure
angle_per_layer = 15  # Degrees of rotation for each layer

def generate_layer(layer_index):
    total_height = 2  # Overall height of the structure
    square_size = 2  # Length of each square layer
    layer_thickness = total_height / layers_count  # Thickness of each layer

    height_position = layer_index * layer_thickness

    bpy.ops.mesh.primitive_cube_add(
        size=square_size,
        location=(0, 0, height_position)
    )

    layer = bpy.context.object
    layer.scale[2] = layer_thickness / 2

    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(layer_index * angle_per_layer),
        orient_axis='Z'
    )

    return layer

for index in range(layers_count):
    generate_layer(index)
