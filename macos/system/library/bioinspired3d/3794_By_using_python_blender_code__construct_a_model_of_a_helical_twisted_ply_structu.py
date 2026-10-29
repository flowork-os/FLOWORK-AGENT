# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_python_blender_code__construct_a_model_of_a_helical_twisted_ply_structu" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using python blender code, construct a model of a helical twisted ply structure made of rectangular fibers. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

number_of_layers = 7  # Number of layers in the helical structure
increment_angle = 10  # Incremental rotation per layer
fiber_shape_type = 'rect'  # Shape of the fibers

height_of_structure = 2.0
size_of_plate = 2.0
thickness_of_layer = height_of_structure / number_of_layers  # Thickness of each layer
spacing_between_fibers = 0.01  # Gap between fibers

def place_fiber(shape_type, diameter, x_pos, y_pos, z_pos, layer_thickness):
    if shape_type == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        fiber_object = bpy.context.object
        fiber_object.dimensions = (layer_thickness, diameter, size_of_plate)
        return fiber_object

def construct_layer(layer_index):
    z_position = layer_index * thickness_of_layer
    rotation_angle = layer_index * increment_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty_object = bpy.context.object

    fiber_diameter = thickness_of_layer
    fiber_distance = fiber_diameter + spacing_between_fibers
    total_fibers = max(1, int(size_of_plate / fiber_distance))

    total_distance = total_fibers * fiber_distance
    initial_y_position = -size_of_plate / 2 + fiber_distance / 2 + (size_of_plate - total_distance) / 2

    for i in range(total_fibers):
        fiber_center_y = initial_y_position + i * fiber_distance
        fiber_instance = place_fiber(
            shape_type=fiber_shape_type,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_center_y,
            z_pos=z_position,
            layer_thickness=thickness_of_layer
        )
        fiber_instance.parent = layer_empty_object
        fiber_instance.matrix_parent_inverse = layer_empty_object.matrix_world.inverted()

    layer_empty_object.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty_object

for layer in range(number_of_layers):
    construct_layer(layer)
