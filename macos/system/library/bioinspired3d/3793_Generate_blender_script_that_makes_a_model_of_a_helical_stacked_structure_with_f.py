# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_script_that_makes_a_model_of_a_helical_stacked_structure_with_f" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender script that makes a model of a helical stacked structure with flat rectangular struts in each layer think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Total number of layers
angle_per_layer = 5  # Degrees of rotation for each layer
fiber_type = 'rect'  # Type of fiber shape

# Dimensions of the overall structure
structure_height = 2
plate_dimension = 2
layer_height = structure_height / layers_count  # Height of each layer
fiber_spacing = 0.01  # Space between fibers

def create_fiber(shape, diameter, x_pos, y_pos, z_pos, height):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        fiber = bpy.context.object
        fiber.dimensions = (height, diameter, plate_dimension)
        return fiber

def generate_layer(layer_index):
    z_position = layer_index * layer_height
    rotation_angle = layer_index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_height
    spacing_between_fibers = fiber_diameter + fiber_spacing
    fiber_count = max(1, int(plate_dimension / spacing_between_fibers))

    total_spacing = fiber_count * spacing_between_fibers
    start_y_position = -plate_dimension / 2 + spacing_between_fibers / 2 + (plate_dimension - total_spacing) / 2

    for i in range(fiber_count):
        fiber_y_center = start_y_position + i * spacing_between_fibers
        fiber_instance = create_fiber(
            shape=fiber_type,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_center,
            z_pos=z_position,
            height=layer_height
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Generate the complete structure
for index in range(layers_count):
    generate_layer(index)
