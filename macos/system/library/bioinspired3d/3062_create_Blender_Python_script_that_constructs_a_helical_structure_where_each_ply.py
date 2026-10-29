# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_Blender_Python_script_that_constructs_a_helical_structure_where_each_ply" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create Blender Python script that constructs a helical structure where each ply consists of rectangular fibers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for a helical fiber structure
ply_number = 9
angle_increment = 7
fiber_shape_type = 'rect'

# Dimensions of the structure
structure_height = 2
plate_area = 2
ply_thickness = structure_height / ply_number
fiber_gap_distance = 0.01

def generate_fiber(fiber_shape_type, diameter, position, thickness):
    if fiber_shape_type == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=position,
            rotation=(0, math.radians(90), 0)
        )
        fiber_obj = bpy.context.object
        fiber_obj.dimensions = (thickness, diameter, plate_area)
        return fiber_obj

def construct_layer(layer_index):
    z_position = layer_index * ply_thickness
    rotation_angle = layer_index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_object = bpy.context.object

    fiber_diameter = ply_thickness
    fiber_count = max(1, int(plate_area / (fiber_diameter + fiber_gap_distance)))

    total_fiber_space = fiber_count * (fiber_diameter + fiber_gap_distance)
    start_y_position = -plate_area / 2 + (fiber_gap_distance / 2) + (plate_area - total_fiber_space) / 2

    for i in range(fiber_count):
        fiber_y_position = start_y_position + i * (fiber_diameter + fiber_gap_distance)
        fiber_instance = generate_fiber(
            fiber_shape_type=fiber_shape_type,
            diameter=fiber_diameter,
            position=(0, fiber_y_position, z_position),
            thickness=ply_thickness
        )
        fiber_instance.parent = empty_object
        fiber_instance.matrix_parent_inverse = empty_object.matrix_world.inverted()

    empty_object.rotation_euler[2] = math.radians(rotation_angle)
    return empty_object

# Generate the entire structure
for index in range(ply_number):
    construct_layer(index)
