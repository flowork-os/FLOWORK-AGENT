# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_python_blender_code_that_builds_a_helical_stacked_bioinspired_structure_w" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create python blender code that builds a helical stacked bioinspired structure where each ply consists of cylindrical fibers. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 12  # Number of layers
rotation_step = 15  # Rotation degrees per layer
fiber_style = 'cylinder'  # Fiber shape type

total_height = 2  # Overall height of the structure
square_plate_size = 2  # Size of each square plate
layer_height = total_height / layer_count  # Height of each layer

def create_fiber(style, diameter, x_coord, y_coord, z_coord):
    if style == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=square_plate_size,
            location=(x_coord, y_coord, z_coord),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def construct_layer(layer_index):
    height_position = layer_index * layer_height
    rotation_angle = layer_index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_position))
    empty_layer = bpy.context.object

    fiber_diameter = layer_height
    fiber_quantity = max(1, int(square_plate_size / fiber_diameter))

    total_fiber_width = fiber_quantity * fiber_diameter
    extra_space = square_plate_size - total_fiber_width
    initial_y = -square_plate_size / 2 + (fiber_diameter / 2) + (extra_space / 2)

    for i in range(fiber_quantity):
        fiber_y_position = initial_y + i * fiber_diameter
        fiber_instance = create_fiber(
            style=fiber_style,
            diameter=fiber_diameter,
            x_coord=0,
            y_coord=fiber_y_position,
            z_coord=height_position
        )
        fiber_instance.parent = empty_layer
        fiber_instance.location = (0, fiber_y_position, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_layer
    empty_layer.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return empty_layer

for i in range(layer_count):
    construct_layer(i)
