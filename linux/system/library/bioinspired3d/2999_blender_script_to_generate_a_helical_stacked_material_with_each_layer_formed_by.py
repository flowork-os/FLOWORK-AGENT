# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_to_generate_a_helical_stacked_material_with_each_layer_formed_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script to generate a helical stacked material with each layer formed by rectangular fibers.

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
plies = 8  # Number of plies in the model
rotation_step = 10  # Rotation in degrees for each ply
fiber_form = 'rect'  # Type of fiber to use

# Dimensions of the helical structure
height = 2.0  # Total height of the structure
plate_dim = 2.0  # Dimension of each plate
thickness_per_ply = height / plies  # Thickness for each ply
spacing_between_fibers = 0.01  # Distance between fibers


def add_fiber_to_scene(shape_type, diameter, x_pos, y_pos, z_pos, thickness):
    if shape_type == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, plate_dim)
        return cube


def generate_plate(plate_index):
    # Function to create a helical plate
    z_position = plate_index * thickness_per_ply
    rotation_angle = plate_index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_obj = bpy.context.object

    fiber_diameter = thickness_per_ply
    fiber_gap = fiber_diameter + spacing_between_fibers
    total_fiber_count = max(1, int(plate_dim / fiber_gap))

    total_fiber_space = total_fiber_count * fiber_gap
    initial_y = -plate_dim / 2 + fiber_gap / 2 + (plate_dim - total_fiber_space) / 2

    for i in range(total_fiber_count):
        fiber_y_position = initial_y + i * fiber_gap
        fiber_instance = add_fiber_to_scene(
            shape_type=fiber_form,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_position,
            z_pos=z_position,
            thickness=thickness_per_ply
        )
        fiber_instance.parent = empty_obj
        fiber_instance.matrix_parent_inverse = empty_obj.matrix_world.inverted()

    empty_obj.rotation_euler[2] = math.radians(rotation_angle)
    return empty_obj

# Construct the helical structure
for i in range(plies):
    generate_plate(i)
