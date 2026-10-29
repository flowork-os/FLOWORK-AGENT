# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_script_that_builds_a_helical_bioinspired_material_with_each_layer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender script that builds a helical bioinspired material with each layer formed by rectangular fibers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical structure
layer_count = 9  # Number of layers in the structure
angle_per_layer = 20  # Rotation angle in degrees for each layer
fiber_shape_type = "rect"  # Fiber shape

# Dimensions of the structure
height_of_structure = 2  # Total height of the complete structure
size_of_each_plate = 2  # Width and length of each square plate
thickness_of_each_layer = height_of_structure / layer_count  # Thickness of each layer
fiber_distance = 0.01  # Small gap between fibers

def add_fiber_shape(shape_type, diameter, x_loc, y_loc, z_loc, thickness):
    if shape_type == "rect":
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_loc, y_loc, z_loc),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, size_of_each_plate)
        return cube


def create_helical_layer(layer_index):
    # Function to create a layer of fibers in a helical arrangement

    height_position = layer_index * thickness_of_each_layer
    rotation_angle = layer_index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_position))
    empty_layer = bpy.context.object

    fiber_diameter = thickness_of_each_layer
    spacing = fiber_diameter + fiber_distance
    fiber_num = max(1, int(size_of_each_plate / spacing))

    total_spacing = fiber_num * spacing
    initial_y = -size_of_each_plate / 2 + spacing / 2 + (size_of_each_plate - total_spacing) / 2

    for i in range(fiber_num):
        fiber_y_center = initial_y + i * spacing
        fiber_instance = add_fiber_shape(
            shape_type=fiber_shape_type,
            diameter=fiber_diameter,
            x_loc=0,
            y_loc=fiber_y_center,
            z_loc=height_position,
            thickness=thickness_of_each_layer
        )
        fiber_instance.parent = empty_layer
        fiber_instance.matrix_parent_inverse = empty_layer.matrix_world.inverted()

    empty_layer.rotation_euler[2] = math.radians(rotation_angle)
    return empty_layer

# Build the helical structure
for index in range(layer_count):
    create_helical_layer(index)
