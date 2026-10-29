# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_for_building_a_helical_twisted_ply_structure_with_flat_rectangula" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code for building a helical twisted ply structure with flat rectangular struts in each layer

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure settings
layer_amount = 9  # Total layers
rotation_increment = 6  # Rotation for each layer
fiber_style = 'rect'  # Type of fiber

# Dimensions of the structure
full_height = 2.0  # Overall height
plate_dimension = 2.0  # Size of each plate
layer_thickness = full_height / layer_amount  # Thickness of each layer
fiber_spacing = 0.01  # Space between fibers

# Function to add a fiber
def place_fiber(style, diameter, x_pos, y_pos, z_pos, thickness):
    if style == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        fiber_instance = bpy.context.object
        fiber_instance.dimensions = (thickness, diameter, plate_dimension)
        return fiber_instance

# Function to create a layer of fibers
def construct_layer(layer_index):
    # Builds a layer in the helical structure
    z_position = layer_index * layer_thickness
    current_rotation = layer_index * rotation_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_layer = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_spacing_between = fiber_diameter + fiber_spacing
    fiber_count = max(1, int(plate_dimension / fiber_spacing_between))

    total_fiber_space = fiber_count * fiber_spacing_between
    start_y_position = -plate_dimension / 2 + fiber_spacing_between / 2 + (plate_dimension - total_fiber_space) / 2

    for i in range(fiber_count):
        fiber_y_position = start_y_position + i * fiber_spacing_between
        fiber_instance = place_fiber(
            style=fiber_style,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_position,
            z_pos=z_position,
            thickness=layer_thickness
        )
        fiber_instance.parent = empty_layer
        fiber_instance.matrix_parent_inverse = empty_layer.matrix_world.inverted()

    empty_layer.rotation_euler[2] = math.radians(current_rotation)
    return empty_layer

# Create the helical structure
for layer_index in range(layer_amount):
    construct_layer(layer_index)
