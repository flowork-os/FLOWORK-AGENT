# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_a_helical_stacked_bioinspired_material_in_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of a helical stacked bioinspired material in blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure configuration
plys = 6  # Total number of plies
angle_step = 18  # Degrees of rotation per ply

# Function to construct each ply
def construct_ply(index):
    total_structure_height = 2  # Height of the complete structure
    cube_dimensions = 2  # Dimension of the square plate
    ply_height = total_structure_height / plys  # Thickness of each ply

    z_position = index * ply_height  # Calculate vertical position

    bpy.ops.mesh.primitive_cube_add(size=cube_dimensions, location=(0, 0, z_position))
    new_plate = bpy.context.object
    new_plate.scale[2] = ply_height / 2  # Scale to make it thin

    bpy.context.view_layer.objects.active = new_plate
    new_plate.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(index * angle_step), orient_axis='Z')

# Generate the helical model
for idx in range(plys):
    construct_ply(idx)
