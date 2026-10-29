# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_Blender_Python_script_that_creates_a_model_of_a_helical_bioinspired_struct" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write Blender Python script that creates a model of a helical bioinspired structure with flat rectangular struts in each layer.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber formation
num_layers = 10  # Total number of layers
angle_increment = 15  # Degrees of rotation for each layer
fiber_style = 'rect'  # Shape of the fibers

# Structure dimensions
complete_height = 2  # Overall height of the structure
plate_side_length = 2  # Length of each plate
thickness_of_layer = complete_height / num_layers  # Thickness of each layer
fiber_separation = 0.01  # Space between fibers

def add_fiber_shape(style, diameter, x_loc, y_loc, z_loc, layer_thickness):
    if style == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_loc, y_loc, z_loc), rotation=(0, math.radians(90), 0))
        fiber_shape = bpy.context.object
        fiber_shape.dimensions = (layer_thickness, diameter, plate_side_length)
        return fiber_shape

def create_layer(layer_index):
    z_position = layer_index * thickness_of_layer
    rotation_angle = layer_index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_layer = bpy.context.object

    fiber_diameter = thickness_of_layer
    distance_between_fibers = fiber_diameter + fiber_separation
    total_fibers = max(1, int(plate_side_length / distance_between_fibers))

    total_fiber_length = total_fibers * distance_between_fibers
    initial_y_position = -plate_side_length / 2 + distance_between_fibers / 2 + (plate_side_length - total_fiber_length) / 2

    for i in range(total_fibers):
        fiber_y_position = initial_y_position + i * distance_between_fibers
        fiber_instance = add_fiber_shape(
            style=fiber_style,
            diameter=fiber_diameter,
            x_loc=0,
            y_loc=fiber_y_position,
            z_loc=z_position,
            layer_thickness=thickness_of_layer
        )
        fiber_instance.parent = empty_layer
        fiber_instance.matrix_parent_inverse = empty_layer.matrix_world.inverted()

    empty_layer.rotation_euler[2] = math.radians(rotation_angle)
    return empty_layer

# Construct the helical structure
for i in range(num_layers):
    create_layer(i)
