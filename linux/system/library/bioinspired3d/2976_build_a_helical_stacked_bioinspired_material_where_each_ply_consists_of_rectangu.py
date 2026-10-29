# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_helical_stacked_bioinspired_material_where_each_ply_consists_of_rectangu" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a helical stacked bioinspired material where each ply consists of rectangular fibers using a Blender script

import bpy
import math

# Clear previous objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
num_layers = 9  # Number of layers in the helical structure
angle_increment = 20  # Degrees of rotation for each layer
fiber_shape = 'rect'  # Shape of the fibers

# Overall dimensions
total_height = 2.0  # Height of the structure
plate_dimension = 2.0  # Size of each plate
layer_height = total_height / num_layers  # Height of each layer
fiber_spacing = 0.01  # Gap between fibers

# Function to create a fiber
def create_fiber(shape, diameter, x, y, z, height):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        fiber_cube = bpy.context.object
        fiber_cube.dimensions = (height, diameter, plate_dimension)
        return fiber_cube

# Function to construct a layer
def construct_layer(layer_index):
    z_position = layer_index * layer_height
    rotation_angle = layer_index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_height
    fiber_count = max(1, int(plate_dimension / (fiber_diameter + fiber_spacing)))

    total_spacing = fiber_count * (fiber_diameter + fiber_spacing)
    start_y = -plate_dimension / 2 + (fiber_diameter + fiber_spacing) / 2 + (plate_dimension - total_spacing) / 2

    for i in range(fiber_count):
        fiber_y_position = start_y + i * (fiber_diameter + fiber_spacing)
        fiber_instance = create_fiber(
            shape=fiber_shape,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y_position,
            z=z_position,
            height=layer_height
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Generate the helical structure
for i in range(num_layers):
    construct_layer(i)
