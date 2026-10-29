# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_to_generate_a_helical_material_made_of_cylindrical_fibers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender to generate a helical material made of cylindrical fibers.

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the fiber structure
ply_count = 12  # Number of plies in the structure
angle_increment = 5  # Degrees of rotation for each ply
fiber_shape_type = 'cylinder'  # Fiber shape

# Dimensions of the overall structure
structure_full_height = 2.0  # Total height
plate_dimensions = 2.0  # Plate width and length
thickness_of_each_ply = structure_full_height / ply_count  # Thickness


def create_fiber_shape(shape_type, diameter, x_pos, y_pos, z_pos):
    if shape_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimensions,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object


def generate_ply(ply_index):
    # Generates a ply of fibers in a helical formation.
    z_position = ply_index * thickness_of_each_ply
    current_rotation = ply_index * angle_increment

    # Create an empty object for fiber grouping
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_ply = bpy.context.object

    fiber_diameter = thickness_of_each_ply
    fiber_quantity = max(1, int(plate_dimensions / fiber_diameter))

    total_fiber_area = fiber_quantity * fiber_diameter
    remaining_area = plate_dimensions - total_fiber_area
    initial_y_position = -plate_dimensions / 2 + (fiber_diameter / 2) + (remaining_area / 2)

    for i in range(fiber_quantity):
        fiber_y_position = initial_y_position + i * fiber_diameter
        fiber_object = create_fiber_shape(
            shape_type=fiber_shape_type,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_position,
            z_pos=z_position
        )
        fiber_object.parent = empty_ply
        fiber_object.location = (0, fiber_y_position, 0)

    # Select the empty object and rotate it
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_ply
    empty_ply.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(current_rotation),
        orient_axis='Z'
    )

    return empty_ply

# Construct the helical structure
for index in range(ply_count):
    generate_ply(index)
