# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_python_blender_code__build_a_model_of_a_helical_stacked_bioinspired_str" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using python blender code, build a model of a helical stacked bioinspired structure with flat rectangular struts in each layer.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure configuration
layers = 6  # Number of layers in the structure
rotation_angle = 12  # Rotation angle for each layer
fiber_style = "rect"

# Dimensions of the structure
complete_height = 2  # Height of the entire structure
plate_length = 2  # Length and width of each plate
layer_height = complete_height / layers  # Height of each layer
fiber_space = 0.01  # Space between fibers

def insert_fiber(style, diameter, x, y, z, height):
    if style == "rect":
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        fiber = bpy.context.object
        fiber.dimensions = (height, diameter, plate_length)
        return fiber

def build_layer(layer_index):
    # Builds a layer of fibers in a helical arrangement.

    current_height = layer_index * layer_height
    current_rotation = layer_index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, current_height))
    layer_empty = bpy.context.object

    fiber_diameter = layer_height
    gap_between_fibers = fiber_diameter + fiber_space
    count_of_fibers = max(1, int(plate_length / gap_between_fibers))

    total_needed_space = count_of_fibers * gap_between_fibers
    starting_y_position = -plate_length / 2 + gap_between_fibers / 2 + (plate_length - total_needed_space) / 2

    for i in range(count_of_fibers):
        fiber_y_position = starting_y_position + i * gap_between_fibers
        fiber_instance = insert_fiber(
            style=fiber_style,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y_position,
            z=current_height,
            height=layer_height
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(current_rotation)
    return layer_empty

# Create the helical structure
for i in range(layers):
    build_layer(i)
