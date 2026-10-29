# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_to_make_a_helical_Bouligand_structure_where_each_ply_consi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script to make a helical Bouligand structure where each ply consists of rectangular fibers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for helical fiber structure
layer_count = 8  # Total number of layers
layer_rotation = 20  # Rotation angle for each layer
fiber_type = 'rect'  # Type of fiber

# Overall dimensions
structure_height = 2  # Total height of the structure
plate_size = 2  # Size of the plate
layer_thickness = structure_height / layer_count  # Thickness of each layer
fiber_gap = 0.01  # Gap between fibers


def add_fiber(type, diameter, x_pos, y_pos, z_pos, thickness):
    if type == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_pos, y_pos, z_pos), rotation=(0, math.radians(90), 0))
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, plate_size)
        return cube


def create_layer(index):
    # Create a layer of fibers in a helical pattern
    z_position = index * layer_thickness
    rotation_angle = index * layer_rotation

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    distance_between_fibers = fiber_diameter + fiber_gap
    number_of_fibers = max(1, int(plate_size / distance_between_fibers))

    total_fiber_space = number_of_fibers * distance_between_fibers
    start_y_position = -plate_size / 2 + distance_between_fibers / 2 + (plate_size - total_fiber_space) / 2

    for i in range(number_of_fibers):
        fiber_y_center = start_y_position + i * distance_between_fibers
        fiber_instance = add_fiber(type=fiber_type, diameter=fiber_diameter, x_pos=0, y_pos=fiber_y_center, z_pos=z_position, thickness=layer_thickness)
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Build the entire structure
for i in range(layer_count):
    create_layer(i)
