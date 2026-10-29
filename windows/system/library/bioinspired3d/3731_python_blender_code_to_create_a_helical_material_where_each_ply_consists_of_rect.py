# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_create_a_helical_material_where_each_ply_consists_of_rect" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to create a helical material where each ply consists of rectangular fibers Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the fiber helix
layer_count = 14  # Number of layers
rotation_increment = 20  # Degrees of rotation per layer
fiber_kind = 'rect'  # Type of fiber

# Dimensions for the structure
height_of_structure = 2.0  # Total height
plate_side = 2.0  # Width and length of each plate
thickness_of_layer = height_of_structure / layer_count  # Thickness of each layer
spacing_between_fibers = 0.01  # Gap between fibers


def insert_fiber(shape, diameter, x_coord, y_coord, z_coord, thickness):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_coord, y_coord, z_coord),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, plate_side)
        return cube


def create_layer(layer_index):
    z_position = layer_index * thickness_of_layer
    rotation_angle = layer_index * rotation_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = thickness_of_layer
    fiber_gap = fiber_diameter + spacing_between_fibers
    fiber_count = max(1, int(plate_side / fiber_gap))

    occupied_area = fiber_count * fiber_gap
    start_y = -plate_side / 2 + fiber_gap / 2 + (plate_side - occupied_area) / 2

    for j in range(fiber_count):
        fiber_y_position = start_y + j * fiber_gap
        fiber_instance = insert_fiber(
            shape=fiber_kind,
            diameter=fiber_diameter,
            x_coord=0,
            y_coord=fiber_y_position,
            z_coord=z_position,
            thickness=thickness_of_layer
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Generate the structure
for i in range(layer_count):
    create_layer(i)
