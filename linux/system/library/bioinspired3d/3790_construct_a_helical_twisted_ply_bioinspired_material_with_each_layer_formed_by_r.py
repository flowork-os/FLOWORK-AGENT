# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_helical_twisted_ply_bioinspired_material_with_each_layer_formed_by_r" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a helical twisted ply bioinspired material with each layer formed by rectangular fibers using python blender code think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for helical fiber assembly
layer_count = 12
angle_increment = 5
fiber_geometry = 'rect'

# Dimensions of the assembly
assembly_height = 2
square_plate_size = 2
layer_thickness = assembly_height / layer_count
fiber_gap_distance = 0.01

def create_fiber_structure(fiber_geometry, fiber_radius, position, height):
    if fiber_geometry == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=position,
            rotation=(0, math.radians(90), 0)
        )
        fiber = bpy.context.object
        fiber.dimensions = (height, fiber_radius, square_plate_size)
        return fiber

def add_layer(layer_index):
    z_position = layer_index * layer_thickness
    rotation_angle = layer_index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_radius = layer_thickness
    fiber_count = max(1, int(square_plate_size / (fiber_radius + fiber_gap_distance)))

    total_fiber_length = fiber_count * (fiber_radius + fiber_gap_distance)
    start_y_position = -square_plate_size / 2 + (fiber_gap_distance / 2) + (square_plate_size - total_fiber_length) / 2

    for i in range(fiber_count):
        fiber_y_position = start_y_position + i * (fiber_radius + fiber_gap_distance)
        fiber_instance = create_fiber_structure(
            fiber_geometry=fiber_geometry,
            fiber_radius=fiber_radius,
            position=(0, fiber_y_position, z_position),
            height=layer_thickness
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Generate the entire helical assembly
for index in range(layer_count):
    add_layer(index)
