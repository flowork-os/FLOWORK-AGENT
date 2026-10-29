# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_constructs_a_model_of_a_helical_structure_with_each_layer_fo" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that constructs a model of a helical structure with each layer formed by rectangular fibers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the fiber helical structure
layer_amount = 9  # Number of layers
angle_step = 12  # Degrees of rotation for each layer
fiber_style = 'rect'  # Shape of the fiber

# Dimensions of the structure
full_height = 2.0  # Height of the structure
square_dimension = 2.0  # Dimensions of each plate
layer_height = full_height / layer_amount  # Height of each layer
fiber_gap = 0.01  # Gap between fibers

# Function to create a fiber
def create_fiber_object(shape_type, diameter, x_coord, y_coord, z_coord, thickness):
    if shape_type == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_coord, y_coord, z_coord), rotation=(0, math.radians(90), 0))
        fiber_instance = bpy.context.object
        fiber_instance.dimensions = (thickness, diameter, square_dimension)
        return fiber_instance

# Function to create a layer of fibers
def create_fiber_layer(index):
    z_position = index * layer_height
    rotation_angle = index * angle_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_height
    spacing_between_fibers = fiber_diameter + fiber_gap
    fiber_count = max(1, int(square_dimension / spacing_between_fibers))

    total_fiber_space = fiber_count * spacing_between_fibers
    start_y = -square_dimension / 2 + spacing_between_fibers / 2 + (square_dimension - total_fiber_space) / 2

    for i in range(fiber_count):
        fiber_center_y = start_y + i * spacing_between_fibers
        fiber_instance = create_fiber_object(fiber_style, fiber_diameter, 0, fiber_center_y, z_position, layer_height)
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Generate the helical structure
for i in range(layer_amount):
    create_fiber_layer(i)
