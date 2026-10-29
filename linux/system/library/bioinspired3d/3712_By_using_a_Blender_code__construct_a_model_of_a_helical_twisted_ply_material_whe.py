# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_code__construct_a_model_of_a_helical_twisted_ply_material_whe" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender code, construct a model of a helical twisted ply material where each ply consists of rectangular fibers. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure setup
layer_num = 6  # Number of layers in the design
rotation_step = 12  # Rotation in degrees for each layer
fiber_form_type = 'rect'  # Fiber form

# Structure dimensions
overall_height = 2  # Total height of the helical structure
plate_dimension = 2  # Dimensions of each plate
layer_thickness_value = overall_height / layer_num  # Thickness of each layer
fiber_gap_value = 0.01  # Gap between fibers

def create_fiber_shape(form_type, diameter, x_position, y_position, z_position, thickness_value):
    if form_type == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_position, y_position, z_position),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (thickness_value, diameter, plate_dimension)
        return cube

def build_helical_layer(layer_index):
    z_position = layer_index * layer_thickness_value
    rotation_angle = layer_index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_radius = layer_thickness_value
    fiber_distance = fiber_radius + fiber_gap_value
    fiber_count = max(1, int(plate_dimension / fiber_distance))

    total_fiber_space = fiber_count * fiber_distance
    start_y_position = -plate_dimension / 2 + fiber_distance / 2 + (plate_dimension - total_fiber_space) / 2

    for i in range(fiber_count):
        fiber_y_coord = start_y_position + i * fiber_distance
        fiber_instance = create_fiber_shape(
            form_type=fiber_form_type,
            diameter=fiber_radius,
            x_position=0,
            y_position=fiber_y_coord,
            z_position=z_position,
            thickness_value=layer_thickness_value
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Generate the helical structure
for index in range(layer_num):
    build_helical_layer(index)
