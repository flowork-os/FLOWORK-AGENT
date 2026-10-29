# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_code_generate_a_model_of_a_helical_twisted_ply_material_made_of" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender code generate a model of a helical twisted ply material made of rectangular fibers. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical fiber structure
ply_count = 12  # Number of plies in the structure
rotation_angle_per_ply = 15  # Degrees of rotation for each ply
fiber_style = "rect"  # Fiber shape

# Dimensions of the structure
total_height = 2  # Total height of the structure
plate_dimension = 2  # Size of each square plate
thickness_per_ply = total_height / ply_count  # Thickness of each ply
fiber_gap_distance = 0.01  # Gap between fibers

def create_fiber_object(style, diameter, x_pos, y_pos, z_pos, thickness):
    if style == "rect":
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, plate_dimension)
        return cube

def generate_helical_plate(index):
    z_position = index * thickness_per_ply
    rotation = index * rotation_angle_per_ply

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_object = bpy.context.object

    fiber_diameter = thickness_per_ply
    spacing_between_fibers = fiber_diameter + fiber_gap_distance
    fiber_quantity = max(1, int(plate_dimension / spacing_between_fibers))

    total_fiber_area = fiber_quantity * spacing_between_fibers
    start_y_position = -plate_dimension / 2 + spacing_between_fibers / 2 + (plate_dimension - total_fiber_area) / 2

    for i in range(fiber_quantity):
        fiber_center_y = start_y_position + i * spacing_between_fibers
        fiber_instance = create_fiber_object(
            style=fiber_style,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_center_y,
            z_pos=z_position,
            thickness=thickness_per_ply
        )
        fiber_instance.parent = empty_object
        fiber_instance.matrix_parent_inverse = empty_object.matrix_world.inverted()

    empty_object.rotation_euler[2] = math.radians(rotation)
    return empty_object

# Construct the helical structure
for i in range(ply_count):
    generate_helical_plate(i)
