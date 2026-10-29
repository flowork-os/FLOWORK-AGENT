# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_code_build_a_model_of_a_helical_stacked_bioinspired_structure_made" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender code build a model of a helical stacked bioinspired structure made of rectangular fibers Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 12  # Total layers in the structure
increment_angle = 5  # Degrees of rotation for each layer
fiber_form = 'rect'  # Shape of fibers

complete_height = 2.0  # Total height
square_plate_size = 2.0  # Size of the plates
layer_thickness = complete_height / layer_count  # Thickness of each layer
spacing_between_fibers = 0.01  # Gap between fibers

def add_fiber(form, diameter, x_pos, y_pos, z_pos, thickness):
    if form == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        fiber_cube = bpy.context.object
        fiber_cube.dimensions = (thickness, diameter, square_plate_size)
        return fiber_cube

def create_layer(index):
    height_offset = index * layer_thickness
    rotation_angle = index * increment_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_offset))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_count = max(1, int(square_plate_size / (fiber_diameter + spacing_between_fibers)))

    total_fiber_space = fiber_count * (fiber_diameter + spacing_between_fibers)
    start_y = -square_plate_size / 2 + (fiber_diameter + spacing_between_fibers) / 2 + (square_plate_size - total_fiber_space) / 2

    for i in range(fiber_count):
        fiber_y_position = start_y + i * (fiber_diameter + spacing_between_fibers)
        fiber_instance = add_fiber(
            form=fiber_form,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_position,
            z_pos=height_offset,
            thickness=layer_thickness
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

for i in range(layer_count):
    create_layer(i)
