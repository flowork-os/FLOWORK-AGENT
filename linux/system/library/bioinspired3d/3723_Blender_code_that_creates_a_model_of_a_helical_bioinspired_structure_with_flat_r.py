# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_that_creates_a_model_of_a_helical_bioinspired_structure_with_flat_r" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code that creates a model of a helical bioinspired structure with flat rectangular struts in each layer. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Total number of layers
angle_per_layer = 15  # Degrees of rotation for each layer
fiber_type = 'rectangular'  # Type of fiber shape

# Dimensions of the overall structure
height_total = 2.0  # Height of the entire structure
plate_dimension = 2.0  # Dimensions of each plate
layer_thickness = height_total / layers_count  # Thickness for each layer
fiber_spacing = 0.01  # Space between fibers

def create_fiber(shape, diameter, x_pos, y_pos, z_pos, thickness):
    if shape == 'rectangular':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_pos, y_pos, z_pos), rotation=(0, math.radians(90), 0))
        new_fiber = bpy.context.object
        new_fiber.dimensions = (thickness, diameter, plate_dimension)
        return new_fiber

def generate_layer(layer_index):
    height_offset = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_offset))
    layer_empty = bpy.context.object

    diameter = layer_thickness
    spacing = diameter + fiber_spacing
    fiber_count = max(1, int(plate_dimension / spacing))

    total_fiber_space = fiber_count * spacing
    initial_y = -plate_dimension / 2 + spacing / 2 + (plate_dimension - total_fiber_space) / 2

    for i in range(fiber_count):
        fiber_y_center = initial_y + i * spacing
        fiber_instance = create_fiber(fiber_type, diameter, 0, fiber_y_center, height_offset, layer_thickness)
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Build the full structure
for layer in range(layers_count):
    generate_layer(layer)
