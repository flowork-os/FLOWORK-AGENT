# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_helical_structure_made_of_rectangular_fibers_in_blender_script_think_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a helical structure made of rectangular fibers in blender script think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical fiber assembly
num_layers = 7  # Number of layers in the design
rotation_step = 15  # Rotation per layer in degrees
fiber_shape_type = "rect"

# Dimensions of the entire structure
height_of_structure = 2  # Total height
plate_dimension = 2  # Each plate's width and length
thickness_of_layer = height_of_structure / num_layers  # Layer thickness
fiber_gap_distance = 0.01  # Distance between fibers

def place_fiber(shape_type, diameter, x, y, z, thickness):
    if shape_type == "rect":
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        new_fiber = bpy.context.object
        new_fiber.dimensions = (thickness, diameter, plate_dimension)
        return new_fiber

def construct_layer(layer_index):
    current_height = layer_index * thickness_of_layer
    current_rotation = layer_index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, current_height))
    layer_empty_object = bpy.context.object

    fiber_diameter = thickness_of_layer
    fiber_spacing = fiber_diameter + fiber_gap_distance
    total_fibers = max(1, int(plate_dimension / fiber_spacing))

    total_space_needed = total_fibers * fiber_spacing
    initial_y_position = -plate_dimension / 2 + fiber_spacing / 2 + (plate_dimension - total_space_needed) / 2

    for i in range(total_fibers):
        fiber_y_coord = initial_y_position + i * fiber_spacing
        fiber_instance = place_fiber(
            shape_type=fiber_shape_type,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y_coord,
            z=current_height,
            thickness=thickness_of_layer
        )
        fiber_instance.parent = layer_empty_object
        fiber_instance.matrix_parent_inverse = layer_empty_object.matrix_world.inverted()

    layer_empty_object.rotation_euler[2] = math.radians(current_rotation)
    return layer_empty_object

# Create the helical structure
for i in range(num_layers):
    construct_layer(i)
