# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_makes_a_helical_bioinspired_structure_made_of_rectangular_fi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that makes a helical bioinspired structure made of rectangular fibers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure parameters
num_layers = 8  # Number of layers in the design
rotation_angle = 12  # Degrees of rotation per layer
fiber_shape_type = 'rect'  # Shape of fibers

# Structure dimensions
height_of_structure = 2  # Total height of the structure
plate_size = 2  # Width and length of each plate
layer_thickness = height_of_structure / num_layers  # Thickness of each layer
spacing_between_fibers = 0.01  # Small gap between fibers


def create_fiber(type_of_fiber, diameter, x_coord, y_coord, z_coord, thickness):
    if type_of_fiber == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_coord, y_coord, z_coord),
            rotation=(0, math.radians(90), 0)
        )
        fiber = bpy.context.object
        fiber.dimensions = (thickness, diameter, plate_size)
        return fiber


def generate_helical_layer(layer_index):
    # Generate a layer of fibers in a helical arrangement.

    z_position = layer_index * layer_thickness
    rotation_angle_value = layer_index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_spacing = fiber_diameter + spacing_between_fibers
    fiber_count = max(1, int(plate_size / fiber_spacing))

    total_fiber_length = fiber_count * fiber_spacing
    start_y = -plate_size / 2 + fiber_spacing / 2 + (plate_size - total_fiber_length) / 2

    for i in range(fiber_count):
        fiber_center_y = start_y + i * fiber_spacing
        fiber_object = create_fiber(
            type_of_fiber=fiber_shape_type,
            diameter=fiber_diameter,
            x_coord=0,
            y_coord=fiber_center_y,
            z_coord=z_position,
            thickness=layer_thickness
        )
        fiber_object.parent = layer_empty
        fiber_object.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle_value)
    return layer_empty

# Construct the helical structure
for index in range(num_layers):
    generate_helical_layer(index)
