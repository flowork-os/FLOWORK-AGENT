# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_for_making_a_helical_twisted_ply_bioinspired_structure_with_each_la" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code for making a helical twisted ply bioinspired structure with each layer formed by rectangular fibers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber arrangement parameters
num_layers = 7  # Total layers
angle_increment = 10  # Angle of rotation for each layer
fiber_form = 'rectangle'  # Shape of the fibers

# Dimensions for the overall structure
height_of_structure = 2  # Height of the structure
plate_dimensions = 2  # Each plate's width and length
layer_thickness = height_of_structure / num_layers  # Thickness calculation
spacing_between_fibers = 0.01  # Gap between fibers


def create_fiber_shape(fiber_shape, diameter, x_pos, y_pos, z_pos, thickness):
    if fiber_shape == 'rectangle':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        fiber = bpy.context.object
        fiber.dimensions = (thickness, diameter, plate_dimensions)
        return fiber


def construct_layer(layer_index):
    # Construct a layer of fibers in helical form.

    z_position = layer_index * layer_thickness
    rotation_angle = layer_index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_spacing = fiber_diameter + spacing_between_fibers
    number_of_fibers = max(1, int(plate_dimensions / fiber_spacing))

    total_fiber_space = number_of_fibers * fiber_spacing
    start_y = -plate_dimensions / 2 + fiber_spacing / 2 + (plate_dimensions - total_fiber_space) / 2

    for i in range(number_of_fibers):
        center_y = start_y + i * fiber_spacing
        fiber_object = create_fiber_shape(
            fiber_shape=fiber_form,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=center_y,
            z_pos=z_position,
            thickness=layer_thickness
        )
        fiber_object.parent = layer_empty
        fiber_object.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Build the structure
for index in range(num_layers):
    construct_layer(index)
