# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_to_build_a_model_of_a_helical_structure_with_flat_rectangu" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script to build a model of a helical structure with flat rectangular struts in each layer.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure settings
number_of_layers = 6  # Layers in the structure
angle_per_layer = 18  # Degrees of rotation for each layer
fiber_shape = 'rect'

# Dimensions of the structure
total_height = 2  # Height of the complete structure
size_of_plate = 2  # Width and length of each plate
layer_thickness = total_height / number_of_layers  # Thickness of a single layer
fiber_spacing = 0.01  # Gap between fibers


def insert_fiber(shape, diameter, x, y, z, thickness):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z), rotation=(0, math.radians(90), 0))
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, size_of_plate)
        return cube


def construct_layer(index):
    # Construct a layer of fibers arranged in a helical manner
    z_position = index * layer_thickness
    rotation_angle = index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_layer = bpy.context.object

    fiber_diameter = layer_thickness
    distance_between_fibers = fiber_diameter + fiber_spacing
    total_fibers = max(1, int(size_of_plate / distance_between_fibers))

    available_space = total_fibers * distance_between_fibers
    initial_y_position = -size_of_plate / 2 + distance_between_fibers / 2 + (size_of_plate - available_space) / 2

    for i in range(total_fibers):
        fiber_y_center = initial_y_position + i * distance_between_fibers
        fiber_instance = insert_fiber(shape=fiber_shape, diameter=fiber_diameter, x=0, y=fiber_y_center, z=z_position, thickness=layer_thickness)
        fiber_instance.parent = empty_layer
        fiber_instance.matrix_parent_inverse = empty_layer.matrix_world.inverted()

    empty_layer.rotation_euler[2] = math.radians(rotation_angle)
    return empty_layer

# Create the complete structure
for i in range(number_of_layers):
    construct_layer(i)
