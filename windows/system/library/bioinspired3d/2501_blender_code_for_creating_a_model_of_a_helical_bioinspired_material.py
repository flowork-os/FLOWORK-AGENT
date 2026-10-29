# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_for_creating_a_model_of_a_helical_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code for creating a model of a helical bioinspired material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical structure
plys = 9  # Number of plies
rotation_angle = 3  # Angle of rotation per ply

def build_helical_structure(plies, rotation):
    height_total = 2
    cube_size = 2
    individual_thickness = height_total / plies

    for i in range(plies):
        z_pos = i * individual_thickness
        bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_pos))
        current_cube = bpy.context.object
        current_cube.scale[2] = individual_thickness / 2
        bpy.context.view_layer.objects.active = current_cube
        current_cube.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(i * rotation), orient_axis='Z')

build_helical_structure(plys, rotation_angle)
