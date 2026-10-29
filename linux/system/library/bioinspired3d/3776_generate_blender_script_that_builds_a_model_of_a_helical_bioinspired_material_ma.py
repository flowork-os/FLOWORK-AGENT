# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_script_that_builds_a_model_of_a_helical_bioinspired_material_ma" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender script that builds a model of a helical bioinspired material made of rectangular fibers think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 15  # Total number of layers
rotation_step = 10  # Degrees of rotation for each layer
fiber_style = 'rect'  # Shape of fibers

complete_height = 2  # Total height of the structure
plate_dim = 2  # Width and length of each square plate
layer_height = complete_height / layer_count  # Height of each layer
fiber_spacing_distance = 0.01  # Gap between fibers

def add_fiber_shape(style, diameter, x, y, z, height):
    if style == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (height, diameter, plate_dim)
        return cube

def construct_helical_layer(layer_index):
    z_position = layer_index * layer_height
    angle_for_layer = layer_index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_layer = bpy.context.object

    fiber_diameter = layer_height
    fiber_distance = fiber_diameter + fiber_spacing_distance
    total_fiber_count = max(1, int(plate_dim / fiber_distance))

    total_fiber_space = total_fiber_count * fiber_distance
    start_y_coord = -plate_dim / 2 + fiber_distance / 2 + (plate_dim - total_fiber_space) / 2

    for j in range(total_fiber_count):
        fiber_y_center = start_y_coord + j * fiber_distance
        fiber_instance = add_fiber_shape(
            style=fiber_style,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y_center,
            z=z_position,
            height=layer_height
        )
        fiber_instance.parent = empty_layer
        fiber_instance.matrix_parent_inverse = empty_layer.matrix_world.inverted()

    empty_layer.rotation_euler[2] = math.radians(angle_for_layer)
    return empty_layer

for idx in range(layer_count):
    construct_helical_layer(idx)
