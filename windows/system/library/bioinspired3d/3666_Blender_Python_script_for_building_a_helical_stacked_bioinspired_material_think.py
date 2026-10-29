# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_for_building_a_helical_stacked_bioinspired_material_think" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script for building a helical stacked bioinspired material think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

total_layers = 8
rotation_angle = 10

def add_helical_plate(index):
    full_height = 2
    plate_dimension = 2
    thickness_per_plate = full_height / total_layers

    current_height = index * thickness_per_plate

    bpy.ops.mesh.primitive_cube_add(size=plate_dimension, location=(0, 0, current_height))
    new_plate = bpy.context.object
    new_plate.scale[2] = thickness_per_plate / 2

    bpy.context.view_layer.objects.active = new_plate
    new_plate.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(index * rotation_angle), orient_axis='Z')

for i in range(total_layers):
    add_helical_plate(i)
