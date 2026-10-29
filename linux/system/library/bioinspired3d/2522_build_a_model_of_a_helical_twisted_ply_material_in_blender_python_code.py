# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_a_helical_twisted_ply_material_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of a helical twisted ply material in blender python code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for helical model
ply_count = 7  # Number of plies/layers
angle_increment = 20  # Degrees of rotation per ply

def add_helical_plate(index):
    total_height = 2  # Height of the entire structure
    cube_size = 2  # Size of each square plate
    thickness_per_ply = total_height / ply_count  # Thickness of each ply

    z_position = index * thickness_per_ply  # Position along Z-axis

    bpy.ops.mesh.primitive_cube_add(
        size=cube_size,
        location=(0, 0, z_position)
    )

    plate = bpy.context.object
    plate.scale[2] = thickness_per_ply / 2  # Scale to make it thin

    bpy.context.view_layer.objects.active = plate
    plate.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(index * angle_increment),
        orient_axis='Z'
    )

for i in range(ply_count):
    add_helical_plate(i)
