# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_blender_code_that_makes_a_model_of_a_helical_stacked_bioinspired_structu" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a blender code that makes a model of a helical stacked bioinspired structure with each layer formed by rectangular fibers Think step by step.

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure configuration
num_layers = 7  # Total layers
rotation_angle = 10  # Rotation per layer
fiber_shape_type = "rect"

# Dimensions
total_height = 2
square_plate_size = 2
layer_height = total_height / num_layers  # Height of each layer
fiber_space = 0.01  # Space between fibers

# Function to add a fiber
def place_fiber(shape_type, diameter, x_coord, y_coord, z_coord, height):
    if shape_type == "rect":
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_coord, y_coord, z_coord),
            rotation=(0, math.radians(90), 0)
        )
        fiber = bpy.context.object
        fiber.dimensions = (height, diameter, square_plate_size)
        return fiber

# Function to create a layer of fibers
def build_layer(layer_idx):
    z_position = layer_idx * layer_height
    rotation_for_layer = layer_idx * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_layer = bpy.context.object

    fiber_diameter = layer_height
    fiber_distance = fiber_diameter + fiber_space
    total_fibers = max(1, int(square_plate_size / fiber_distance))

    total_fiber_length = total_fibers * fiber_distance
    start_y_coord = -square_plate_size / 2 + fiber_distance / 2 + (square_plate_size - total_fiber_length) / 2

    for i in range(total_fibers):
        y_center = start_y_coord + i * fiber_distance
        fiber_obj = place_fiber(
            shape_type=fiber_shape_type,
            diameter=fiber_diameter,
            x_coord=0,
            y_coord=y_center,
            z_coord=z_position,
            height=layer_height
        )
        fiber_obj.parent = empty_layer
        fiber_obj.matrix_parent_inverse = empty_layer.matrix_world.inverted()

    empty_layer.rotation_euler[2] = math.radians(rotation_for_layer)
    return empty_layer

# Create the helical structure
for i in range(num_layers):
    build_layer(i)
