# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_a_helical_twisted_ply_bioinspired_structure_using_blender_python" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of a helical twisted ply bioinspired structure using blender python code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
plies = 8  # Number of plies in the helical structure
rotation_angle = 12  # Rotation angle for each ply

def create_helical_plates(total_plies, rotation):
    total_height = 2
    plate_size = 2
    thickness = total_height / total_plies

    for i in range(total_plies):
        z_position = i * thickness
        bpy.ops.mesh.primitive_cube_add(size=plate_size, location=(0, 0, z_position))
        plate = bpy.context.object
        plate.scale[2] = thickness / 2
        bpy.ops.transform.rotate(value=math.radians(i * rotation), orient_axis='Z')

# Build the helical structure
create_helical_plates(plies, rotation_angle)
