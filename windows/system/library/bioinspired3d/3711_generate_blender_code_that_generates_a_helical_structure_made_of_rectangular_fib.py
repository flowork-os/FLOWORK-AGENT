# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_code_that_generates_a_helical_structure_made_of_rectangular_fib" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender code that generates a helical structure made of rectangular fibers. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical fiber structure
layer_count = 8  # Total layers in the structure
rotation_increment = 20  # Incremental rotation per layer in degrees
fiber_style = 'rect'  # Style of fibers

# Overall structure dimensions
complete_height = 2  # Height of the entire structure
single_plate_size = 2  # Size of each square plate
layer_height = complete_height / layer_count  # Height of each layer
fiber_space = 0.01  # Space between fibers


def insert_fiber(style, diameter, x_coord, y_coord, z_coord, height):
    if style == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_coord, y_coord, z_coord),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (height, diameter, single_plate_size)
        return cube


def generate_layer(index):
    # Generate a layer of helical fibers

    height_position = index * layer_height
    angle_value = index * rotation_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_position))
    layer_empty = bpy.context.object

    fiber_radius = layer_height
    distance_between = fiber_radius + fiber_space
    fiber_quantity = max(1, int(single_plate_size / distance_between))

    total_fiber_space = fiber_quantity * distance_between
    start_y_coord = -single_plate_size / 2 + distance_between / 2 + (single_plate_size - total_fiber_space) / 2

    for i in range(fiber_quantity):
        fiber_y_coord = start_y_coord + i * distance_between
        fiber_instance = insert_fiber(
            style=fiber_style,
            diameter=fiber_radius,
            x_coord=0,
            y_coord=fiber_y_coord,
            z_coord=height_position,
            height=layer_height
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(angle_value)
    return layer_empty

# Create the structure
for idx in range(layer_count):
    generate_layer(idx)
