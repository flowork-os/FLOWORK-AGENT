# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_generating_a_model_of_a_helical_material_with_flat_recta" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for generating a model of a helical material with flat rectangular struts in each layer.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for constructing a helical fiber structure
layers_count = 10  # Total number of layers
angle_per_layer = 15  # Degrees of rotation for each layer
fiber_type = 'rect'

# Dimensions of the overall structure
structure_height = 2
plate_dimension = 2
layer_thickness = structure_height / layers_count  # Thickness of each layer
fiber_separation = 0.01  # Space between fibers

def construct_fiber(fiber_type, diameter, x_pos, y_pos, z_pos, thickness):
    if fiber_type == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, plate_dimension)
        return cube


def generate_layer(layer_index):
    # Function to create a helical layer of fibers
    z_position = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_layer = bpy.context.object

    fiber_diameter = layer_thickness
    spacing_between_fibers = fiber_diameter + fiber_separation
    fiber_count = max(1, int(plate_dimension / spacing_between_fibers))

    total_fiber_space = fiber_count * spacing_between_fibers
    start_y_position = -plate_dimension / 2 + spacing_between_fibers / 2 + (plate_dimension - total_fiber_space) / 2

    for i in range(fiber_count):
        fiber_y_center = start_y_position + i * spacing_between_fibers
        fiber_instance = construct_fiber(
            fiber_type=fiber_type,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_center,
            z_pos=z_position,
            thickness=layer_thickness
        )
        fiber_instance.parent = empty_layer
        fiber_instance.matrix_parent_inverse = empty_layer.matrix_world.inverted()

    empty_layer.rotation_euler[2] = math.radians(rotation_angle)
    return empty_layer

# Build the entire structure
for index in range(layers_count):
    generate_layer(index)
