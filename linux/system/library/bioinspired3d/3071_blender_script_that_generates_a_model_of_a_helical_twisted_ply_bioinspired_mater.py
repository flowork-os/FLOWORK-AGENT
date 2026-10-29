# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_generates_a_model_of_a_helical_twisted_ply_bioinspired_mater" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that generates a model of a helical twisted ply bioinspired material with each layer formed by rectangular fibers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
layer_count = 10
rotation_increment = 15
fiber_geometry = 'rect'

# Structure dimensions
overall_height = 2.0
plate_dim = 2.0
layer_height = overall_height / layer_count
fiber_separation = 0.01


def add_helical_fiber(geometry, diameter, x_pos, y_pos, z_pos, height):
    if geometry == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_pos, y_pos, z_pos), rotation=(0, math.radians(90), 0))
        fiber = bpy.context.object
        fiber.dimensions = (height, diameter, plate_dim)
        return fiber


def generate_helical_layer(layer_index):
    # Generates a helical layer of fibers.
    z_position = layer_index * layer_height
    rotation_angle = layer_index * rotation_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_layer = bpy.context.object

    fiber_diameter = layer_height
    spacing_between_fibers = fiber_diameter + fiber_separation
    fiber_total_count = max(1, int(plate_dim / spacing_between_fibers))

    total_fiber_area = fiber_total_count * spacing_between_fibers
    start_y_coord = -plate_dim / 2 + spacing_between_fibers / 2 + (plate_dim - total_fiber_area) / 2

    for i in range(fiber_total_count):
        fiber_y_coord = start_y_coord + i * spacing_between_fibers
        fiber_instance = add_helical_fiber(fiber_geometry, fiber_diameter, 0, fiber_y_coord, z_position, layer_height)
        fiber_instance.parent = empty_layer
        fiber_instance.matrix_parent_inverse = empty_layer.matrix_world.inverted()

    empty_layer.rotation_euler[2] = math.radians(rotation_angle)
    return empty_layer

# Create the helical structure
for layer in range(layer_count):
    generate_helical_layer(layer)
