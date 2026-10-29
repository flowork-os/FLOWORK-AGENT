# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_blender_code_construct_a_model_of_a_helical_structure_with_each_layer_for" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a blender code construct a model of a helical structure with each layer formed by rectangular fibers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for fiber structure
layer_count = 9  # Total number of layers
rotation_increment = 20  # Degree of rotation for each layer
fiber_form_type = 'rect'  # Type of fiber shape

# Dimensions of the structure
structure_height_total = 2  # Total height of the structure
individual_plate_size = 2  # Size of each plate
layer_thickness_value = structure_height_total / layer_count  # Thickness of each layer
fiber_gap_value = 0.01  # Space between fibers


def create_fiber_shape(type_of_fiber, diameter, x_position, y_position, z_position, thickness):
    if type_of_fiber == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_position, y_position, z_position),
            rotation=(0, math.radians(90), 0)
        )
        fiber_shape = bpy.context.object
        fiber_shape.dimensions = (thickness, diameter, individual_plate_size)
        return fiber_shape


def construct_helical_layer(layer_index):
    # Create a layer of fibers in a helical formation.

    z_position = layer_index * layer_thickness_value
    rotation_angle = layer_index * rotation_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness_value
    fiber_spacing = fiber_diameter + fiber_gap_value
    fiber_quantity = max(1, int(individual_plate_size / fiber_spacing))

    total_spacing = fiber_quantity * fiber_spacing
    start_y_position = -individual_plate_size / 2 + fiber_spacing / 2 + (individual_plate_size - total_spacing) / 2

    for i in range(fiber_quantity):
        fiber_center_y = start_y_position + i * fiber_spacing
        fiber_object = create_fiber_shape(
            type_of_fiber=fiber_form_type,
            diameter=fiber_diameter,
            x_position=0,
            y_position=fiber_center_y,
            z_position=z_position,
            thickness=layer_thickness_value
        )
        fiber_object.parent = layer_empty
        fiber_object.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Build the entire structure
for index in range(layer_count):
    construct_helical_layer(index)
