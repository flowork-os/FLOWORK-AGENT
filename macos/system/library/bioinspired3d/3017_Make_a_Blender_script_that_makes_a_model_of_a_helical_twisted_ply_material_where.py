# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_Blender_script_that_makes_a_model_of_a_helical_twisted_ply_material_where" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a Blender script that makes a model of a helical twisted ply material where each ply consists of rectangular fibers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the fiber helical structure
ply_count = 6  # Total number of plies
rotation_angle_per_ply = 7  # Angle of rotation for each ply
fiber_style = 'rect'  # Fiber shape

# Dimensions of the structure
structure_height = 2.0  # Height of the entire structure
plate_dimension = 2.0  # Width and length of each plate
thickness_of_ply = structure_height / ply_count  # Thickness of each ply
fiber_gap_distance = 0.01  # Gap between fibers

def add_fiber_shape(fiber_style, fiber_diameter, position):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=position, rotation=(0, math.radians(90), 0))
    fiber = bpy.context.object
    fiber.dimensions = (thickness_of_ply, fiber_diameter, plate_dimension)
    return fiber


def create_ply(index):
    z_position = index * thickness_of_ply
    rotation_for_ply = index * rotation_angle_per_ply

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_ply = bpy.context.object

    fiber_diameter = thickness_of_ply
    fiber_spacing = fiber_diameter + fiber_gap_distance
    fiber_count = max(1, int(plate_dimension / fiber_spacing))

    total_fiber_space = fiber_count * fiber_spacing
    start_y_position = -plate_dimension / 2 + fiber_spacing / 2 + (plate_dimension - total_fiber_space) / 2

    for i in range(fiber_count):
        fiber_center_y = start_y_position + i * fiber_spacing
        fiber_instance = add_fiber_shape(
            fiber_style=fiber_style,
            fiber_diameter=fiber_diameter,
            position=(0, fiber_center_y, z_position)
        )
        fiber_instance.parent = empty_ply
        fiber_instance.matrix_parent_inverse = empty_ply.matrix_world.inverted()

    empty_ply.rotation_euler[2] = math.radians(rotation_for_ply)
    return empty_ply

# Generate the helical structure
for i in range(ply_count):
    create_ply(i)
