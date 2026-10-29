# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_that_generates_a_helical_stacked_bioinspired_structure_wit" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code that generates a helical stacked bioinspired structure with each layer formed by rectangular fibers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical structure
plies_count = 12  # Number of plies
rotation_angle = 5  # Angle per ply in degrees
fiber_shape = 'rect'

# Dimensions
total_height = 2  # Full height of the structure
plate_dimension = 2  # Size of each plate
ply_height = total_height / plies_count  # Height of each ply
fiber_distance = 0.01  # Distance between fibers


def create_fiber(shape, diameter, x, y, z, height):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z), rotation=(0, math.radians(90), 0))
        cube = bpy.context.object
        cube.dimensions = (height, diameter, plate_dimension)
        return cube


def build_plate(index):
    # Build a helical plate with fibers
    z_position = index * ply_height
    angle = index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_plate = bpy.context.object

    fiber_diameter = ply_height
    spacing = fiber_diameter + fiber_distance
    total_fibers = max(1, int(plate_dimension / spacing))

    available_space = total_fibers * spacing
    start_y = -plate_dimension / 2 + spacing / 2 + (plate_dimension - available_space) / 2

    for i in range(total_fibers):
        fiber_y = start_y + i * spacing
        fiber_instance = create_fiber(shape=fiber_shape, diameter=fiber_diameter, x=0, y=fiber_y, z=z_position, height=ply_height)
        fiber_instance.parent = empty_plate
        fiber_instance.matrix_parent_inverse = empty_plate.matrix_world.inverted()

    empty_plate.rotation_euler[2] = math.radians(angle)
    return empty_plate

# Construct the entire structure
for layer in range(plies_count):
    build_plate(layer)
