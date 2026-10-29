# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_helical_twisted_ply_structure_made_of_rectangular_fibers_in_blender_p" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a helical twisted ply structure made of rectangular fibers in blender python code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure parameters
layers = 10  # Number of layers
rotation_step = 15  # Rotation per layer in degrees
fiber_kind = 'rect'  # Fiber shape

# Dimensions of the structure
height_of_structure = 2  # Complete height
plate_dimension = 2  # Dimension of each plate
layer_height = height_of_structure / layers  # Height of each layer
fiber_spacing_distance = 0.01  # Distance between fibers

def create_fiber_object(fiber_kind, diameter, x_loc, y_loc, z_loc, layer_height):
    if fiber_kind == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_loc, y_loc, z_loc), rotation=(0, math.radians(90), 0))
        fiber_cube = bpy.context.object
        fiber_cube.dimensions = (layer_height, diameter, plate_dimension)
        return fiber_cube

def construct_layer(layer_index):
    z_coordinate = layer_index * layer_height
    rotation_angle = layer_index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_coordinate))
    layer_empty = bpy.context.object

    fiber_diameter = layer_height
    fiber_gap = fiber_diameter + fiber_spacing_distance
    fiber_count = max(1, int(plate_dimension / fiber_gap))

    total_fiber_space = fiber_count * fiber_gap
    start_y_coordinate = -plate_dimension / 2 + fiber_gap / 2 + (plate_dimension - total_fiber_space) / 2

    for i in range(fiber_count):
        fiber_y_position = start_y_coordinate + i * fiber_gap
        fiber_instance = create_fiber_object(
            fiber_kind=fiber_kind,
            diameter=fiber_diameter,
            x_loc=0,
            y_loc=fiber_y_position,
            z_loc=z_coordinate,
            layer_height=layer_height
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Generate the helical structure
for i in range(layers):
    construct_layer(i)
