# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_to_create_a_model_of_a_helical_Bouligand_material__Think_step_by_st" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code to create a model of a helical Bouligand material. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 15
angle_per_layer = 20

def create_helical_model():
    total_height = 2
    square_length = 2
    thickness = total_height / layer_count

    for i in range(layer_count):
        z_position = i * thickness
        bpy.ops.mesh.primitive_cube_add(size=square_length, location=(0, 0, z_position))
        plate = bpy.context.object
        plate.scale[2] = thickness / 2
        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(i * angle_per_layer), orient_axis='Z')

create_helical_model()
