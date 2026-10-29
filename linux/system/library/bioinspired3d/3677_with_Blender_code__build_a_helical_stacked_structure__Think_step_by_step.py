# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_Blender_code__build_a_helical_stacked_structure__Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with Blender code, build a helical stacked structure. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
layers = 12
angle_step = 10

def add_helical_plate(index):
    # Create a plate for the helical design
    height_of_structure = 2
    plate_dimension = 2
    thickness_of_layer = height_of_structure / layers

    z_position = index * thickness_of_layer
    bpy.ops.mesh.primitive_cube_add(size=plate_dimension, location=(0, 0, z_position))
    plate = bpy.context.object
    plate.scale[2] = thickness_of_layer / 2

    bpy.context.view_layer.objects.active = plate
    plate.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(index * angle_step), orient_axis='Z')

for i in range(layers):
    add_helical_plate(i)
