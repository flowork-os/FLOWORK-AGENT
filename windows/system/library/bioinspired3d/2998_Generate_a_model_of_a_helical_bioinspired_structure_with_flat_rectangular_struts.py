# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_a_helical_bioinspired_structure_with_flat_rectangular_struts" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of a helical bioinspired structure with flat rectangular struts in each layer using Blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber assembly
layers_count = 10  # Total layers in the structure
angle_increment = 15  # Degrees of rotation for each layer
fiber_type = 'rect'

# Overall dimensions of the structure
structure_height = 2.0  # Height of the entire assembly
plate_dimension = 2.0  # Length and width of each plate
layer_thickness = structure_height / layers_count  # Thickness of each layer
fiber_spacing = 0.01  # Gap between fibers


def create_fiber(shape, diameter, pos_x, pos_y, pos_z, thickness):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(pos_x, pos_y, pos_z),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, plate_dimension)
        return cube


def build_plate(layer_index):
    # Function to build a helical layer of fibers
    height_offset = layer_index * layer_thickness
    rotation_angle = layer_index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_offset))
    empty_plate = bpy.context.object

    fiber_radius = layer_thickness
    spacing_between_fibers = fiber_radius + fiber_spacing
    total_fibers = max(1, int(plate_dimension / spacing_between_fibers))

    total_length = total_fibers * spacing_between_fibers
    start_y_position = -plate_dimension / 2 + spacing_between_fibers / 2 + (plate_dimension - total_length) / 2

    for j in range(total_fibers):
        fiber_y_position = start_y_position + j * spacing_between_fibers
        fiber_object = create_fiber(
            shape=fiber_type,
            diameter=fiber_radius,
            pos_x=0,
            pos_y=fiber_y_position,
            pos_z=height_offset,
            thickness=layer_thickness
        )
        fiber_object.parent = empty_plate
        fiber_object.matrix_parent_inverse = empty_plate.matrix_world.inverted()

    empty_plate.rotation_euler[2] = math.radians(rotation_angle)
    return empty_plate

# Construct the entire structure
for index in range(layers_count):
    build_plate(index)
