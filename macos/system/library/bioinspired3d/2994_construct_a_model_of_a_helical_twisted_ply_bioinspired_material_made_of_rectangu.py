# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_a_helical_twisted_ply_bioinspired_material_made_of_rectangu" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of a helical twisted ply bioinspired material made of rectangular fibers in a Blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure parameters
num_layers = 7  # Number of layers in the helical structure
angle_increment = 10  # Rotation angle for each layer
fiber_shape_type = 'rect'  # Shape of the fiber

# Overall dimensions
complete_height = 2.0  # Total height of the structure
square_size = 2.0  # Dimensions of each square plate
layer_height = complete_height / num_layers  # Height of each layer
spacing_between_fibers = 0.01  # Gap between fibers

# Function to create a fiber
def create_fiber_object(shape, diameter, x_coord, y_coord, z_coord, thickness):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_coord, y_coord, z_coord), rotation=(0, math.radians(90), 0))
        fiber_object = bpy.context.object
        fiber_object.dimensions = (thickness, diameter, square_size)
        return fiber_object

# Function to create a single layer of fibers
def construct_layer(layer_index):
    z_position = layer_index * layer_height
    rotation_angle = layer_index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty_object = bpy.context.object

    fiber_diameter = layer_height
    fiber_distance = fiber_diameter + spacing_between_fibers
    total_fiber_count = max(1, int(square_size / fiber_distance))

    total_fiber_width = total_fiber_count * fiber_distance
    start_y_position = -square_size / 2 + fiber_distance / 2 + (square_size - total_fiber_width) / 2

    for i in range(total_fiber_count):
        fiber_center_y = start_y_position + i * fiber_distance
        fiber_instance = create_fiber_object(fiber_shape_type, fiber_diameter, 0, fiber_center_y, z_position, layer_height)
        fiber_instance.parent = layer_empty_object
        fiber_instance.matrix_parent_inverse = layer_empty_object.matrix_world.inverted()

    layer_empty_object.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty_object

# Generate the helical structure
for index in range(num_layers):
    construct_layer(index)
