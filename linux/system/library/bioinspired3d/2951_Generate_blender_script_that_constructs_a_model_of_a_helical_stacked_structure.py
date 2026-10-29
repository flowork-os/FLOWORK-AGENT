# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_script_that_constructs_a_model_of_a_helical_stacked_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender script that constructs a model of a helical stacked structure

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical structure parameters
ply_count = 7  # Total number of plies
rotation_angle_per_ply = 12  # Degrees to rotate each ply

def create_helical_structure():
    total_height = 2
    plate_side_length = 2
    thickness_per_ply = total_height / ply_count

    for i in range(ply_count):
        z_position = i * thickness_per_ply
        bpy.ops.mesh.primitive_cube_add(size=plate_side_length, location=(0, 0, z_position))
        plate = bpy.context.object
        plate.scale[2] = thickness_per_ply / 2
        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(i * rotation_angle_per_ply), orient_axis='Z')

# Create the helical structure
create_helical_structure()
