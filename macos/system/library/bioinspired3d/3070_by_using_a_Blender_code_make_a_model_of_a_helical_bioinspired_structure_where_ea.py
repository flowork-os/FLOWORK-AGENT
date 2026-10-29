# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_code_make_a_model_of_a_helical_bioinspired_structure_where_ea" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender code make a model of a helical bioinspired structure where each ply consists of rectangular fibers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the fiber-based helical structure
ply_count = 10
angle_per_ply = 15
fiber_form = 'rect'

# Dimensions of the overall structure
height_total = 2.0
plate_dimension = 2.0
thickness_per_ply = height_total / ply_count
fiber_distance = 0.01


def generate_fiber(shape, diameter, x_pos, y_pos, z_pos, thickness):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_pos, y_pos, z_pos), rotation=(0, math.radians(90), 0))
        cube_instance = bpy.context.object
        cube_instance.dimensions = (thickness, diameter, plate_dimension)
        return cube_instance


def create_helical_ply(ply_index):
    # Creates a ply of fibers in a helical formation.
    z_coord = ply_index * thickness_per_ply
    rotation_angle = ply_index * angle_per_ply

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_coord))
    empty_object = bpy.context.object

    fiber_diameter = thickness_per_ply
    fiber_spacing = fiber_diameter + fiber_distance
    total_fibers = max(1, int(plate_dimension / fiber_spacing))

    total_fiber_spacing = total_fibers * fiber_spacing
    initial_y_coord = -plate_dimension / 2 + fiber_spacing / 2 + (plate_dimension - total_fiber_spacing) / 2

    for i in range(total_fibers):
        fiber_y_position = initial_y_coord + i * fiber_spacing
        fiber_object = generate_fiber(fiber_form, fiber_diameter, 0, fiber_y_position, z_coord, thickness_per_ply)
        fiber_object.parent = empty_object
        fiber_object.matrix_parent_inverse = empty_object.matrix_world.inverted()

    empty_object.rotation_euler[2] = math.radians(rotation_angle)
    return empty_object

# Construct the entire helical structure
for index in range(ply_count):
    create_helical_ply(index)
