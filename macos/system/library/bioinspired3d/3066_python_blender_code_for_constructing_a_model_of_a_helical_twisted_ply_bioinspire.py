# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_constructing_a_model_of_a_helical_twisted_ply_bioinspire" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for constructing a model of a helical twisted ply bioinspired structure with each layer formed by rectangular fibers

import bpy
import math

# Remove all objects in the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the fiber structure
number_of_plies = 8  # Number of plies
angle_increment = 20  # Angle increment for each ply
fiber_style = 'rect'  # Fiber shape

# Structure dimensions
height_of_structure = 2.0
size_of_plate = 2.0
layer_thickness = height_of_structure / number_of_plies  # Thickness of each layer
spacing_between_fibers = 0.01  # Gap between fibers

# Function to add a fiber
def add_fiber(style, diameter, x_loc, y_loc, z_loc, thickness):
    if style == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_loc, y_loc, z_loc),
            rotation=(0, math.radians(90), 0)
        )
        new_fiber = bpy.context.object
        new_fiber.dimensions = (thickness, diameter, size_of_plate)
        return new_fiber

# Function to create a ply
def make_ply(index):
    z_position = index * layer_thickness
    rotation_angle = index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_layer = bpy.context.object

    fiber_diameter = layer_thickness
    distance_between_fibers = fiber_diameter + spacing_between_fibers
    total_fiber_count = max(1, int(size_of_plate / distance_between_fibers))

    total_fiber_space = total_fiber_count * distance_between_fibers
    starting_y = -size_of_plate / 2 + distance_between_fibers / 2 + (size_of_plate - total_fiber_space) / 2

    for i in range(total_fiber_count):
        fiber_y_center = starting_y + i * distance_between_fibers
        fiber_instance = add_fiber(
            style=fiber_style,
            diameter=fiber_diameter,
            x_loc=0,
            y_loc=fiber_y_center,
            z_loc=z_position,
            thickness=layer_thickness
        )
        fiber_instance.parent = empty_layer
        fiber_instance.matrix_parent_inverse = empty_layer.matrix_world.inverted()

    empty_layer.rotation_euler[2] = math.radians(rotation_angle)
    return empty_layer

# Create the entire structure
for i in range(number_of_plies):
    make_ply(i)
