# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_code_in_Blender_that_builds_a_helical_stacked_structure_think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write code in Blender that builds a helical stacked structure think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
ply_count = 9
rotation_degrees = 20

def add_helical_plate(index):
    # Create a helical plate at a specific index
    height = 2
    size = 2
    thickness = height / ply_count
    z_position = index * thickness

    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
    plate = bpy.context.object
    plate.scale[2] = thickness / 2
    bpy.context.view_layer.objects.active = plate
    plate.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(index * rotation_degrees), orient_axis='Z')

# Build the helical structure
for i in range(ply_count):
    add_helical_plate(i)
