# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_build_a_helical_Bouligand_material_with_flat_rectangular" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to build a helical Bouligand material with flat rectangular struts in each layer Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Fiber structure parameters
ply_count = 12  # Number of plies
angle_per_ply = 5  # Rotation angle per ply
fiber_shape_type = 'rect'  # Shape of fibers

# Structure dimensions
total_height = 2  # Complete height
plate_dimension = 2  # Size of the plates
thickness_per_ply = total_height / ply_count  # Thickness of each ply
fiber_spacing_value = 0.01  # Distance between fibers


def add_fiber_shape(shape_type, diameter, x_coord, y_coord, z_coord, thickness):
    if shape_type == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_coord, y_coord, z_coord),
            rotation=(0, math.radians(90), 0)
        )
        fiber = bpy.context.object
        fiber.dimensions = (thickness, diameter, plate_dimension)
        return fiber


def generate_helical_layer(layer_number):
    # Create a helical layer of fibers.

    z_position = layer_number * thickness_per_ply
    rotation_angle = layer_number * angle_per_ply

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_layer = bpy.context.object

    fiber_diameter = thickness_per_ply
    fiber_spacing = fiber_diameter + fiber_spacing_value
    fiber_count = max(1, int(plate_dimension / fiber_spacing))

    total_fiber_length = fiber_count * fiber_spacing
    initial_y = -plate_dimension / 2 + fiber_spacing / 2 + (plate_dimension - total_fiber_length) / 2

    for i in range(fiber_count):
        fiber_center_y = initial_y + i * fiber_spacing
        fiber_obj = add_fiber_shape(
            shape_type=fiber_shape_type,
            diameter=fiber_diameter,
            x_coord=0,
            y_coord=fiber_center_y,
            z_coord=z_position,
            thickness=thickness_per_ply
        )
        fiber_obj.parent = empty_layer
        fiber_obj.matrix_parent_inverse = empty_layer.matrix_world.inverted()

    empty_layer.rotation_euler[2] = math.radians(rotation_angle)
    return empty_layer

# Construct the helical structure
for layer in range(ply_count):
    generate_helical_layer(layer)
