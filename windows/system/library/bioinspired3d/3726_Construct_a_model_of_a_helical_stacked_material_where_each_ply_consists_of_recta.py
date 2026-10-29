# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_a_helical_stacked_material_where_each_ply_consists_of_recta" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of a helical stacked material where each ply consists of rectangular fibers using a Blender script think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
layer_count = 8  # Total number of layers
rotation_increment = 20  # Degrees of rotation for each layer
fiber_shape = 'rect'  # Fiber shape

# Structure dimensions
structure_height = 2.0  # Total height of the structure
plate_dimension = 2.0  # Size of each plate
layer_thickness = structure_height / layer_count  # Thickness of each layer
fiber_distance = 0.01  # Distance between fibers

# Function to create fibers
def create_fiber(shape, diameter, x_pos, y_pos, z_pos, thickness):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_pos, y_pos, z_pos), rotation=(0, math.radians(90), 0))
        fiber_object = bpy.context.object
        fiber_object.dimensions = (thickness, diameter, plate_dimension)
        return fiber_object

# Function to generate a layer of fibers
def generate_fiber_layer(layer_index):
    z_position = layer_index * layer_thickness
    rotation_angle = layer_index * rotation_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    spacing = fiber_diameter + fiber_distance
    number_of_fibers = max(1, int(plate_dimension / spacing))

    total_fiber_space = number_of_fibers * spacing
    start_y = -plate_dimension / 2 + spacing / 2 + (plate_dimension - total_fiber_space) / 2

    for i in range(number_of_fibers):
        fiber_center_y = start_y + i * spacing
        fiber_instance = create_fiber(fiber_shape, fiber_diameter, 0, fiber_center_y, z_position, layer_thickness)
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Build the helical structure
for index in range(layer_count):
    generate_fiber_layer(index)
