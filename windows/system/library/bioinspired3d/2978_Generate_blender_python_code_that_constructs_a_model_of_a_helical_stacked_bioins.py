# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_python_code_that_constructs_a_model_of_a_helical_stacked_bioins" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender python code that constructs a model of a helical stacked bioinspired structure made of rectangular fibers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers = 10  # Number of layers in the structure
angle_per_layer = 15  # Degrees of rotation for each layer
fiber_type = 'rect'  # Type of fibers used

# Dimensions of the overall structure
structure_height = 2  # Total height of the structure
plate_dimension = 2  # Width and length of each square plate
layer_thickness = structure_height / layers  # Thickness of each layer
spacing_between_fibers = 0.01  # Gap between fibers

def create_fiber(fiber_type, diameter, x_pos, y_pos, z_pos, thickness):
    if fiber_type == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, plate_dimension)
        return cube


def build_layer(layer_index):
    # Build a helical layer of fibers

    height_offset = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_offset))
    layer_empty = bpy.context.object

    fiber_radius = layer_thickness
    fiber_distance = fiber_radius + spacing_between_fibers
    total_fibers = max(1, int(plate_dimension / fiber_distance))

    total_fiber_space = total_fibers * fiber_distance
    start_position_y = -plate_dimension / 2 + fiber_distance / 2 + (plate_dimension - total_fiber_space) / 2

    for i in range(total_fibers):
        fiber_y_position = start_position_y + i * fiber_distance
        fiber_instance = create_fiber(
            fiber_type=fiber_type,
            diameter=fiber_radius,
            x_pos=0,
            y_pos=fiber_y_position,
            z_pos=height_offset,
            thickness=layer_thickness
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Generate the entire structure
for index in range(layers):
    build_layer(index)
