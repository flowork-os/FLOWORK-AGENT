# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_python_blender_code_that_constructs_a_helical_twisted_ply_bioinspired_struc" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make python blender code that constructs a helical twisted ply bioinspired structure. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

plies = 7  # Total number of plies
rotation_deg = 12  # Degrees of rotation per ply

def generate_helical_structure():
    total_height = 2  # Complete height of the structure
    side_length = 2  # Length of each square plate
    thickness = total_height / plies  # Thickness of each ply

    for i in range(plies):
        create_ply(i, thickness, side_length)

def create_ply(index, ply_thickness, plate_size):
    z_position = index * ply_thickness
    bpy.ops.mesh.primitive_cube_add(size=plate_size, location=(0, 0, z_position))
    ply = bpy.context.object
    ply.scale[2] = ply_thickness / 2
    bpy.context.view_layer.objects.active = ply
    ply.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(index * rotation_deg), orient_axis='Z')

generate_helical_structure()
