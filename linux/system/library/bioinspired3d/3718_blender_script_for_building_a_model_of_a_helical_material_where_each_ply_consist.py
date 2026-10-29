# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_building_a_model_of_a_helical_material_where_each_ply_consist" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for building a model of a helical material where each ply consists of rectangular fibers. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Total number of layers
angle_per_layer = 15  # Degrees of rotation for each layer
fiber_type = 'rect'  # Type of fiber shape

# Dimensions of the overall structure
structure_height = 2.0  # Height of the entire structure
plate_dimension = 2.0  # Size of each square plate
layer_thickness = structure_height / layers_count  # Thickness of each layer
fiber_spacing = 0.01  # Space between fibers

def create_fiber(shape, diameter, x_pos, y_pos, z_pos, thickness):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_pos, y_pos, z_pos), rotation=(0, math.radians(90), 0))
        fiber = bpy.context.object
        fiber.dimensions = (thickness, diameter, plate_dimension)
        return fiber

def build_layer(layer_index):
    z_position = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    spacing_between_fibers = fiber_diameter + fiber_spacing
    total_fibers = max(1, int(plate_dimension / spacing_between_fibers))

    total_fiber_spacing = total_fibers * spacing_between_fibers
    start_y_position = -plate_dimension / 2 + spacing_between_fibers / 2 + (plate_dimension - total_fiber_spacing) / 2

    for i in range(total_fibers):
        fiber_y_center = start_y_position + i * spacing_between_fibers
        fiber_instance = create_fiber(fiber_type, fiber_diameter, 0, fiber_y_center, z_position, layer_thickness)
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Construct the entire structure
for index in range(layers_count):
    build_layer(index)
