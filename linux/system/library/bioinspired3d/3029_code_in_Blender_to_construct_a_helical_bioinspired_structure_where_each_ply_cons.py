# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_to_construct_a_helical_bioinspired_structure_where_each_ply_cons" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender to construct a helical bioinspired structure where each ply consists of rectangular fibers

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
ply_count = 7  # Total plies in the structure
rotation_step = 10  # Degrees of rotation for each ply
fiber_shape_type = 'rectangle'  # Shape of the fibers

# Dimensions of the final structure
height_of_structure = 2.0  # Overall height
plate_dimension = 2.0  # Dimensions of each plate
thickness_of_ply = height_of_structure / ply_count  # Thickness of each ply
fiber_gap_distance = 0.01  # Distance between fibers

def place_fiber(shape_type, diameter, x_pos, y_pos, z_pos, thickness):
    if shape_type == 'rectangle':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_pos, y_pos, z_pos), rotation=(0, math.radians(90), 0))
        fiber = bpy.context.object
        fiber.dimensions = (thickness, diameter, plate_dimension)
        return fiber

def generate_ply(index):
    # Generate a helical ply layer
    z_position = index * thickness_of_ply
    rotation_angle = index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_object = bpy.context.object

    fiber_diameter = thickness_of_ply
    spacing_between_fibers = fiber_diameter + fiber_gap_distance
    fiber_count = max(1, int(plate_dimension / spacing_between_fibers))

    total_fiber_length = fiber_count * spacing_between_fibers
    initial_y = -plate_dimension / 2 + spacing_between_fibers / 2 + (plate_dimension - total_fiber_length) / 2

    for i in range(fiber_count):
        current_y = initial_y + i * spacing_between_fibers
        fiber_instance = place_fiber(
            shape_type=fiber_shape_type,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=current_y,
            z_pos=z_position,
            thickness=thickness_of_ply
        )
        fiber_instance.parent = empty_object
        fiber_instance.matrix_parent_inverse = empty_object.matrix_world.inverted()

    empty_object.rotation_euler[2] = math.radians(rotation_angle)
    return empty_object

# Building the entire structure
for i in range(ply_count):
    generate_ply(i)
