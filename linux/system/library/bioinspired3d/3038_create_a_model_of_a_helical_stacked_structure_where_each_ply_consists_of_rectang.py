# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_a_helical_stacked_structure_where_each_ply_consists_of_rectang" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of a helical stacked structure where each ply consists of rectangular fibers in Blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Number of layers in the design
angle_per_layer = 15  # Degrees of rotation for each layer
fiber_type = "rect"

# Dimensions of the overall structure
structure_height = 2
plate_dimension = 2
layer_thickness = structure_height / layers_count  # Thickness of each layer
spacing_between_fibers = 0.01  # Gap between fibers

def create_fiber(shape, diameter, x_pos, y_pos, z_pos, thickness):
    if shape == "rect":
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, plate_dimension)
        return cube


def generate_layer(layer_index):
    # Constructs a helical layer composed of fibers.
    height_offset = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_offset))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_spacing = fiber_diameter + spacing_between_fibers
    fiber_count = max(1, int(plate_dimension / fiber_spacing))

    total_fiber_space = fiber_count * fiber_spacing
    start_y_position = -plate_dimension / 2 + fiber_spacing / 2 + (plate_dimension - total_fiber_space) / 2

    for i in range(fiber_count):
        fiber_y_center = start_y_position + i * fiber_spacing
        fiber_instance = create_fiber(
            shape=fiber_type,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_center,
            z_pos=height_offset,
            thickness=layer_thickness
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Build the structure
for i in range(layers_count):
    generate_layer(i)
