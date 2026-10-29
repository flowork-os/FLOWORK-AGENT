# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_to_generate_a_model_of_a_helical_structure_made_of_rectangular_fibe" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code to generate a model of a helical structure made of rectangular fibers

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for fiber structure
num_layers = 12  # Total number of layers
angle_per_layer = 5  # Rotation angle per layer
fiber_shape = 'rect'

# Dimensions for the entire structure
total_height = 2.0  # Height of the structure
plate_size = 2.0  # Dimensions of each plate
layer_height = total_height / num_layers  # Height of each layer
fiber_distance = 0.01  # Gap between fibers


def create_fiber_shape(shape_type, diameter, x_coord, y_coord, z_coord, height):
    if shape_type == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_coord, y_coord, z_coord),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (height, diameter, plate_size)
        return cube


def construct_layer(index):
    # Build a single layer of fibers
    z_position = index * layer_height
    rotation_angle = index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_radius = layer_height
    spacing = fiber_radius + fiber_distance
    total_fibers = max(1, int(plate_size / spacing))

    occupied_space = total_fibers * spacing
    starting_y = -plate_size / 2 + spacing / 2 + (plate_size - occupied_space) / 2

    for j in range(total_fibers):
        current_y = starting_y + j * spacing
        fiber_instance = create_fiber_shape(
            shape_type=fiber_shape,
            diameter=fiber_radius,
            x_coord=0,
            y_coord=current_y,
            z_coord=z_position,
            height=layer_height
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Create the entire fiber structure
for i in range(num_layers):
    construct_layer(i)
