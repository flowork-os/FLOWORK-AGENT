# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_creates_a_model_of_a_helical_stacked_bioinspired_stru" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that creates a model of a helical stacked bioinspired structure with each layer formed by rectangular fibers

import bpy
import math

# Clean the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical fiber assembly
layer_count = 7  # Number of layers in the helical structure
rotation_step = 10  # Rotation in degrees for each layer
fiber_shape_type = 'rectangle'  # Shape of fibers

# Overall dimensions
structure_height = 2.0  # Total height
plate_dimension = 2.0  # Size of each plate
layer_height = structure_height / layer_count  # Height of each layer
fiber_gap_distance = 0.01  # Distance between fibers

# Function to add a fiber
def insert_fiber(shape_type, diameter, x_coord, y_coord, z_coord, height):
    if shape_type == 'rectangle':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_coord, y_coord, z_coord),
            rotation=(0, math.radians(90), 0)
        )
        fiber_object = bpy.context.object
        fiber_object.dimensions = (height, diameter, plate_dimension)
        return fiber_object

# Function to create a single layer
def generate_layer(index):
    # Creates a layer in the helical structure
    z_position = index * layer_height
    rotation_angle = index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_layer = bpy.context.object

    fiber_diameter = layer_height
    fiber_spacing = fiber_diameter + fiber_gap_distance
    total_fibers = max(1, int(plate_dimension / fiber_spacing))

    total_fiber_space = total_fibers * fiber_spacing
    start_y_position = -plate_dimension / 2 + fiber_spacing / 2 + (plate_dimension - total_fiber_space) / 2

    for i in range(total_fibers):
        fiber_y = start_y_position + i * fiber_spacing
        fiber_instance = insert_fiber(
            shape_type=fiber_shape_type,
            diameter=fiber_diameter,
            x_coord=0,
            y_coord=fiber_y,
            z_coord=z_position,
            height=layer_height
        )
        fiber_instance.parent = empty_layer
        fiber_instance.matrix_parent_inverse = empty_layer.matrix_world.inverted()

    empty_layer.rotation_euler[2] = math.radians(rotation_angle)
    return empty_layer

# Build the entire helical structure
for layer_index in range(layer_count):
    generate_layer(layer_index)
