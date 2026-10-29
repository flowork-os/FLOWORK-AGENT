# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_code__build_a_helical_bioinspired_material_made_of_rectangular" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender code, build a helical bioinspired material made of rectangular fibers Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber configuration
ply_count = 12  # Number of plies
rotation_angle = 5  # Degrees of rotation for each ply
fiber_type = 'rect'  # Type of fiber shape

# Structure dimensions
total_height = 2.0  # Complete height of the structure
plate_dimension = 2.0  # Width and length of each plate
thickness_per_ply = total_height / ply_count  # Thickness of each ply
fiber_spacing = 0.01  # Space between fibers

# Function to add a fiber
def add_fiber_object(fiber_shape, fiber_diameter, x_position, y_position, z_position, thickness):
    if fiber_shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_position, y_position, z_position), rotation=(0, math.radians(90), 0))
        fiber_object = bpy.context.object
        fiber_object.dimensions = (thickness, fiber_diameter, plate_dimension)
        return fiber_object

# Function to create a helical layer
def create_helical_layer(index):
    z_offset = index * thickness_per_ply
    rotation_offset = index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_offset))
    helical_empty = bpy.context.object

    fiber_diameter = thickness_per_ply
    spacing_between_fibers = fiber_diameter + fiber_spacing
    fiber_count = max(1, int(plate_dimension / spacing_between_fibers))

    total_spacing = fiber_count * spacing_between_fibers
    start_y_position = -plate_dimension / 2 + spacing_between_fibers / 2 + (plate_dimension - total_spacing) / 2

    for i in range(fiber_count):
        fiber_center_y = start_y_position + i * spacing_between_fibers
        fiber_instance = add_fiber_object(fiber_type, fiber_diameter, 0, fiber_center_y, z_offset, thickness_per_ply)
        fiber_instance.parent = helical_empty
        fiber_instance.matrix_parent_inverse = helical_empty.matrix_world.inverted()

    helical_empty.rotation_euler[2] = math.radians(rotation_offset)
    return helical_empty

# Construct the helical structure
for i in range(ply_count):
    create_helical_layer(i)
