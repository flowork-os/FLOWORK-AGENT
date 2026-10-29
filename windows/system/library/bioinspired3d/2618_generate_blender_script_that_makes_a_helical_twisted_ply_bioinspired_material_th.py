# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_script_that_makes_a_helical_twisted_ply_bioinspired_material_th" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender script that makes a helical twisted ply bioinspired material think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

plys = 7  # Number of plies
rotation_angle = 18  # Angle of rotation per ply

def create_ply(index):
    height_total = 2  # Total height of the structure
    ply_size = 2  # Size of each ply
    ply_thickness = height_total / plys  # Thickness of each ply

    z_position = index * ply_thickness

    bpy.ops.mesh.primitive_cube_add(size=ply_size, location=(0, 0, z_position))
    ply_object = bpy.context.object
    ply_object.scale[2] = ply_thickness / 2

    bpy.context.view_layer.objects.active = ply_object
    ply_object.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(index * rotation_angle), orient_axis='Z')

for i in range(plys):
    create_ply(i)
