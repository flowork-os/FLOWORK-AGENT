# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_python_code_create_a_model_of_a_helical_Bouligand_structure_where_e" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender python code create a model of a helical Bouligand structure where each ply consists of rectangular fibers. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical fiber arrangement
num_layers = 8  # Number of layers in the model
rotation_step = 10  # Rotation angle for each layer
fiber_shape_type = 'rect'  # Shape of the fibers

# Overall dimensions
total_height = 2.0  # Height of the structure
plate_dimension = 2.0  # Dimensions of each square plate
thickness_per_layer = total_height / num_layers  # Layer thickness
fiber_distance = 0.01  # Distance between fibers


def generate_fiber(shape, diameter, x_pos, y_pos, z_pos, thickness):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_pos, y_pos, z_pos), rotation=(0, math.radians(90), 0))
        fiber = bpy.context.object
        fiber.dimensions = (thickness, diameter, plate_dimension)
        return fiber


def create_layer(layer_index):
    z_position = layer_index * thickness_per_layer
    layer_rotation = layer_index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_radius = thickness_per_layer
    spacing_between_fibers = fiber_radius + fiber_distance
    fiber_count = max(1, int(plate_dimension / spacing_between_fibers))

    total_spacing = fiber_count * spacing_between_fibers
    initial_y = -plate_dimension / 2 + spacing_between_fibers / 2 + (plate_dimension - total_spacing) / 2

    for i in range(fiber_count):
        fiber_y_position = initial_y + i * spacing_between_fibers
        fiber_instance = generate_fiber(fiber_shape_type, fiber_radius, 0, fiber_y_position, z_position, thickness_per_layer)
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(layer_rotation)
    return layer_empty

# Build the entire structure
for index in range(num_layers):
    create_layer(index)
