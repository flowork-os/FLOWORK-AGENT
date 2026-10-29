# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_a_helical_stacked_material_in_code_in_Blender_think_step_by_ste" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of a helical stacked material in code in Blender think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
ply_count = 12
rotation_step = 5

def add_helical_plate(index):
    total_height = 2
    square_size = 2
    thickness_per_ply = total_height / ply_count
    z_position = index * thickness_per_ply

    bpy.ops.mesh.primitive_cube_add(size=square_size, location=(0, 0, z_position))
    plate = bpy.context.object
    plate.scale[2] = thickness_per_ply / 2

    bpy.context.view_layer.objects.active = plate
    plate.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(index * rotation_step), orient_axis='Z')

for i in range(ply_count):
    add_helical_plate(i)
