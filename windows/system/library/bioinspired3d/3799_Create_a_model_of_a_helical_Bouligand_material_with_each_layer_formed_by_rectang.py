# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_a_helical_Bouligand_material_with_each_layer_formed_by_rectang" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of a helical Bouligand material with each layer formed by rectangular fibers using Blender code Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure parameters
number_of_layers = 10
rotation_angle = 15
fiber_shape_type = 'rect'

# Dimensions for the overall structure
height_of_structure = 2.0
size_of_plate = 2.0
thickness_of_layer = height_of_structure / number_of_layers
spacing_between_fibers = 0.01

def add_fiber_to_scene(shape_type, diameter, x_pos, y_pos, z_pos, layer_thickness):
    if shape_type == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_pos, y_pos, z_pos), rotation=(0, math.radians(90), 0))
        fiber_object = bpy.context.object
        fiber_object.dimensions = (layer_thickness, diameter, size_of_plate)
        return fiber_object

def construct_layer(layer_index):
    current_height = layer_index * thickness_of_layer
    current_rotation = layer_index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, current_height))
    layer_empty = bpy.context.object

    fiber_diameter = thickness_of_layer
    fiber_gap = fiber_diameter + spacing_between_fibers
    fiber_count = max(1, int(size_of_plate / fiber_gap))

    total_fiber_area = fiber_count * fiber_gap
    start_y_position = -size_of_plate / 2 + fiber_gap / 2 + (size_of_plate - total_fiber_area) / 2

    for i in range(fiber_count):
        fiber_y_coord = start_y_position + i * fiber_gap
        fiber_instance = add_fiber_to_scene(fiber_shape_type, fiber_diameter, 0, fiber_y_coord, current_height, thickness_of_layer)
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(current_rotation)
    return layer_empty

# Build the complete structure
for layer in range(number_of_layers):
    construct_layer(layer)
