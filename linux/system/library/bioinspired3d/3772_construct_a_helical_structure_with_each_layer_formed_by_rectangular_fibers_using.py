# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_helical_structure_with_each_layer_formed_by_rectangular_fibers_using" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a helical structure with each layer formed by rectangular fibers using Blender Python script think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure setup
layer_total = 15  # Number of layers
rotation_increment = 3  # Degree increment for each layer
fiber_shape_type = "rect"

# Overall dimensions
height_structure = 2
size_plate = 2
thickness_layer = height_structure / layer_total  # Layer thickness
fiber_spacing = 0.01  # Space between fibers

def add_fiber_instance(shape, diameter, x_coord, y_coord, z_coord, thickness):
    if shape == "rect":
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_coord, y_coord, z_coord),
            rotation=(0, math.radians(90), 0)
        )
        new_fiber = bpy.context.object
        new_fiber.dimensions = (thickness, diameter, size_plate)
        return new_fiber

def create_layer_structure(layer_index):
    z_position = layer_index * thickness_layer
    layer_rotation = layer_index * rotation_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = thickness_layer
    spacing_between_fibers = fiber_diameter + fiber_spacing
    fiber_count = max(1, int(size_plate / spacing_between_fibers))

    total_length = fiber_count * spacing_between_fibers
    start_y_coord = -size_plate / 2 + spacing_between_fibers / 2 + (size_plate - total_length) / 2

    for i in range(fiber_count):
        fiber_y_center = start_y_coord + i * spacing_between_fibers
        fiber_instance = add_fiber_instance(
            shape=fiber_shape_type,
            diameter=fiber_diameter,
            x_coord=0,
            y_coord=fiber_y_center,
            z_coord=z_position,
            thickness=thickness_layer
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(layer_rotation)
    return layer_empty

# Build the helical structure
for i in range(layer_total):
    create_layer_structure(i)
