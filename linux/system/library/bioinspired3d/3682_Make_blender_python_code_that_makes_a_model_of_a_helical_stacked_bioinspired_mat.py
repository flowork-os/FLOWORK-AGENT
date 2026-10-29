# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_blender_python_code_that_makes_a_model_of_a_helical_stacked_bioinspired_mat" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make blender python code that makes a model of a helical stacked bioinspired material think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 15  # Number of layers in the structure
rotation_angle = 3  # Rotation angle for each layer

def helical_structure(layer_count, rotation_angle):
    total_height = 2
    plate_size = 2
    layer_height = total_height / layer_count

    for i in range(layer_count):
        z_position = i * layer_height
        bpy.ops.mesh.primitive_cube_add(size=plate_size, location=(0, 0, z_position))
        plate = bpy.context.object
        plate.scale[2] = layer_height / 2

        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(i * rotation_angle), orient_axis='Z')

helical_structure(layer_count, rotation_angle)
