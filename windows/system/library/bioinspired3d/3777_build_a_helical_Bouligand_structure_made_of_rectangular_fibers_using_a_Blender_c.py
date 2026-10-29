# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_helical_Bouligand_structure_made_of_rectangular_fibers_using_a_Blender_c" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a helical Bouligand structure made of rectangular fibers using a Blender code think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_amount = 6  # Number of layers in the structure
rotation_increment = 20  # Rotation angle for each layer
fiber_form = 'rect'  # Type of fiber shape

structure_total_height = 2  # Total height of the structure
square_plate_dimension = 2  # Width and length of each square plate
layer_height_value = structure_total_height / layer_amount  # Height of each layer
fiber_gap_value = 0.01  # Small gap between fibers

def create_fiber_shape(form, diameter, x, y, z, height):
    if form == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        cube_object = bpy.context.object
        cube_object.dimensions = (height, diameter, square_plate_dimension)
        return cube_object

def build_helical_layer(index):
    z_position = index * layer_height_value
    rotation_angle = index * rotation_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_object = bpy.context.object

    fiber_diameter = layer_height_value
    fiber_spacing = fiber_diameter + fiber_gap_value
    fiber_count_total = max(1, int(square_plate_dimension / fiber_spacing))

    total_fiber_space = fiber_count_total * fiber_spacing
    start_y_coord = -square_plate_dimension / 2 + fiber_spacing / 2 + (square_plate_dimension - total_fiber_space) / 2

    for j in range(fiber_count_total):
        fiber_y_center = start_y_coord + j * fiber_spacing
        fiber_instance = create_fiber_shape(
            form=fiber_form,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y_center,
            z=z_position,
            height=layer_height_value
        )
        fiber_instance.parent = empty_object
        fiber_instance.matrix_parent_inverse = empty_object.matrix_world.inverted()

    empty_object.rotation_euler[2] = math.radians(rotation_angle)
    return empty_object

for i in range(layer_amount):
    build_helical_layer(i)
