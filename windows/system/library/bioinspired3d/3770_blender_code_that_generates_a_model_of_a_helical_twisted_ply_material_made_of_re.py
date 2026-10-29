# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_that_generates_a_model_of_a_helical_twisted_ply_material_made_of_re" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code that generates a model of a helical twisted ply material made of rectangular fibers. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical structure
layers = 12  # Number of layers in the helical design
angle_increment = 5  # Degrees of rotation for each layer
fiber_form = "rect"

# Dimensions of the structure
overall_height = 2
plate_dimension = 2
layer_height = overall_height / layers  # Height of each layer
fiber_spacing = 0.01  # Gap between fibers

def create_fiber_object(shape, diameter, x_pos, y_pos, z_pos, thickness):
    if shape == "rect":
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        fiber_cube = bpy.context.object
        fiber_cube.dimensions = (thickness, diameter, plate_dimension)
        return fiber_cube

def construct_layer(layer_index):
    height_offset = layer_index * layer_height
    rotation_angle = layer_index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_offset))
    layer_empty = bpy.context.object

    fiber_diameter = layer_height
    fiber_distance = fiber_diameter + fiber_spacing
    fiber_count = max(1, int(plate_dimension / fiber_distance))

    total_fiber_length = fiber_count * fiber_distance
    initial_y_position = -plate_dimension / 2 + fiber_distance / 2 + (plate_dimension - total_fiber_length) / 2

    for i in range(fiber_count):
        fiber_y_center = initial_y_position + i * fiber_distance
        fiber_instance = create_fiber_object(
            shape=fiber_form,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_center,
            z_pos=height_offset,
            thickness=layer_height
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Generate the helical structure
for i in range(layers):
    construct_layer(i)
