# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_that_generates_a_helical_bioinspired_structure_with_each_layer_form" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code that generates a helical bioinspired structure with each layer formed by rectangular fibers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters defining the helical fiber structure
layers_count = 10  # Total number of layers
angle_per_layer = 15  # Degrees of rotation for each layer
fiber_type = 'rect'  # Type of fiber shape

# Overall dimensions of the structure
structure_height = 2.0  # Complete height of the structure
plate_dimension = 2.0  # Size of each plate in width and length
layer_thickness = structure_height / layers_count  # Thickness of individual layers
fiber_spacing = 0.01  # Gap between fibers

def create_fiber(shape, diameter, x_coord, y_coord, z_coord, thickness):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_coord, y_coord, z_coord), rotation=(0, math.radians(90), 0))
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, plate_dimension)
        return cube


def build_layer(layer_index):
    # Constructs a helical layer composed of fibers.
    height_offset = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_offset))
    empty_layer = bpy.context.object

    fiber_diameter = layer_thickness
    spacing_between_fibers = fiber_diameter + fiber_spacing
    total_fibers = max(1, int(plate_dimension / spacing_between_fibers))

    total_fiber_space = total_fibers * spacing_between_fibers
    initial_y = -plate_dimension / 2 + spacing_between_fibers / 2 + (plate_dimension - total_fiber_space) / 2

    for i in range(total_fibers):
        fiber_y_position = initial_y + i * spacing_between_fibers
        fiber_instance = create_fiber(fiber_type, fiber_diameter, 0, fiber_y_position, height_offset, layer_thickness)
        fiber_instance.parent = empty_layer
        fiber_instance.matrix_parent_inverse = empty_layer.matrix_world.inverted()

    empty_layer.rotation_euler[2] = math.radians(rotation_angle)
    return empty_layer

# Generate the entire structure
for index in range(layers_count):
    build_layer(index)
