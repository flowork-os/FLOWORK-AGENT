# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_blender_code_that_constructs_a_helical_stacked_bioinspired_structure_with" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create blender code that constructs a helical stacked bioinspired structure with each layer formed by rectangular fibers. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for helical fiber arrangement
ply_count = 10  # Total number of plies
rotation_angle = 15  # Degrees of rotation for each ply
fiber_shape_type = 'rect'  # Shape of fibers

# Dimensions of the structure
total_height = 2  # Final height of the structure
individual_plate_size = 2  # Size of each plate
thickness_per_ply = total_height / ply_count  # Thickness for each ply
small_gap_between_fibers = 0.01  # Gap between fibers

def insert_fiber(shape_type, diameter, x_pos, y_pos, z_pos, thickness):
    if shape_type == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_pos, y_pos, z_pos), rotation=(0, math.radians(90), 0))
        fiber = bpy.context.object
        fiber.dimensions = (thickness, diameter, individual_plate_size)
        return fiber

def generate_ply(index):
    z_position = index * thickness_per_ply
    current_rotation = index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_plate = bpy.context.object

    fiber_diameter = thickness_per_ply
    fiber_distance = fiber_diameter + small_gap_between_fibers
    fiber_count = max(1, int(individual_plate_size / fiber_distance))

    total_fiber_length = fiber_count * fiber_distance
    initial_y = -individual_plate_size / 2 + fiber_distance / 2 + (individual_plate_size - total_fiber_length) / 2

    for i in range(fiber_count):
        fiber_position_y = initial_y + i * fiber_distance
        fiber_instance = insert_fiber(
            shape_type=fiber_shape_type,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_position_y,
            z_pos=z_position,
            thickness=thickness_per_ply
        )
        fiber_instance.parent = empty_plate
        fiber_instance.matrix_parent_inverse = empty_plate.matrix_world.inverted()

    empty_plate.rotation_euler[2] = math.radians(current_rotation)
    return empty_plate

# Build the entire helical structure
for i in range(ply_count):
    generate_ply(i)
