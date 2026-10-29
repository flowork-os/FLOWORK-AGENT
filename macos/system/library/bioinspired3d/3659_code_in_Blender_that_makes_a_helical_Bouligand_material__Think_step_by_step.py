# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_that_makes_a_helical_Bouligand_material__Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender that makes a helical Bouligand material. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 15
rotation_angle = 12

def generate_helical_structure(layer_count, rotation_angle):
    height_of_structure = 2
    cube_size = 2
    thickness_per_layer = height_of_structure / layer_count

    for i in range(layer_count):
        z_position = i * thickness_per_layer
        bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
        current_cube = bpy.context.object
        current_cube.scale[2] = thickness_per_layer / 2
        bpy.context.view_layer.objects.active = current_cube
        current_cube.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(i * rotation_angle), orient_axis='Z')

generate_helical_structure(layer_count, rotation_angle)
