# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_Blender_script_that_creates_a_helical_stacked_structure__Think_step_by_s" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a Blender script that creates a helical stacked structure. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

total_plies = 9  # Count of plies
angle_per_ply = 14  # Rotation angle per ply

def make_helical_structure():
    height = 2  # Overall height of the structure
    size = 2  # Dimension of each plate
    thickness = height / total_plies  # Thickness of each ply

    for i in range(total_plies):
        create_helical_ply(i, thickness, size)

def create_helical_ply(index, ply_thickness, plate_size):
    z_position = index * ply_thickness
    bpy.ops.mesh.primitive_cube_add(size=plate_size, location=(0, 0, z_position))
    ply = bpy.context.object
    ply.scale[2] = ply_thickness / 2
    bpy.context.view_layer.objects.active = ply
    ply.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(index * angle_per_ply), orient_axis='Z')

make_helical_structure()
