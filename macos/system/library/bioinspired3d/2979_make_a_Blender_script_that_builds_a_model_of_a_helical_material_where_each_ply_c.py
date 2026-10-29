# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_Blender_script_that_builds_a_model_of_a_helical_material_where_each_ply_c" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a Blender script that builds a model of a helical material where each ply consists of rectangular fibers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical fiber assembly
num_layers = 7  # Total layers in the design
rotation_angle = 10  # Angle of rotation per layer in degrees
fiber_form = 'rect'  # Form of the fibers

# Overall dimensions
height_of_structure = 2  # Total height of the helical structure
size_of_plate = 2  # Dimensions of each plate
thickness_of_layer = height_of_structure / num_layers  # Layer thickness
fiber_spacing = 0.01  # Space between fibers

def generate_fiber(form, diameter, x_pos, y_pos, z_pos, thickness):
    if form == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, size_of_plate)
        return cube


def construct_layer(layer_index):
    # Constructs a helical layer of fibers

    z_position = layer_index * thickness_of_layer
    rotation_value = layer_index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_object = bpy.context.object

    fiber_radius = thickness_of_layer
    distance_between_fibers = fiber_radius + fiber_spacing
    total_fibers = max(1, int(size_of_plate / distance_between_fibers))

    total_fiber_area = total_fibers * distance_between_fibers
    start_y_position = -size_of_plate / 2 + distance_between_fibers / 2 + (size_of_plate - total_fiber_area) / 2

    for i in range(total_fibers):
        fiber_y = start_y_position + i * distance_between_fibers
        fiber_instance = generate_fiber(
            form=fiber_form,
            diameter=fiber_radius,
            x_pos=0,
            y_pos=fiber_y,
            z_pos=z_position,
            thickness=thickness_of_layer
        )
        fiber_instance.parent = empty_object
        fiber_instance.matrix_parent_inverse = empty_object.matrix_world.inverted()

    empty_object.rotation_euler[2] = math.radians(rotation_value)
    return empty_object

# Create the helical structure
for i in range(num_layers):
    construct_layer(i)
