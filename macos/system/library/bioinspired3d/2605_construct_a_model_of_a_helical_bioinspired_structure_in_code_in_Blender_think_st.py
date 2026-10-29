# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_a_helical_bioinspired_structure_in_code_in_Blender_think_st" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of a helical bioinspired structure in code in Blender think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

plies = 9
angle_per_ply = 18

def construct_helical_structure(num_plies, rotation_angle):
    height_of_structure = 2
    size_of_plate = 2
    thickness_of_each_ply = height_of_structure / num_plies

    for i in range(num_plies):
        z_position = i * thickness_of_each_ply
        bpy.ops.mesh.primitive_cube_add(size=size_of_plate, location=(0, 0, z_position))
        ply = bpy.context.object
        ply.scale[2] = thickness_of_each_ply / 2
        bpy.context.view_layer.objects.active = ply
        ply.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(i * rotation_angle), orient_axis='Z')

construct_helical_structure(plies, angle_per_ply)
