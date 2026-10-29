# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_python_blender_code_that_builds_a_helical_structure_with_each_layer_formed" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make python blender code that builds a helical structure with each layer formed by rectangular fibers Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure configuration
num_layers = 7  # Total layers in the design
rotation_angle = 10  # Rotation per layer in degrees
fiber_form = "rect"  # Shape of the fibers

# Overall dimensions
height_of_structure = 2  # Complete height
size_of_plate = 2  # Size of each plate
layer_height = height_of_structure / num_layers  # Height of each layer
fiber_spacing = 0.01  # Space between fibers

def generate_fiber(fiber_form, diameter, x_coord, y_coord, z_coord, height):
    if fiber_form == "rect":
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_coord, y_coord, z_coord),
            rotation=(0, math.radians(90), 0)
        )
        fiber_object = bpy.context.object
        fiber_object.dimensions = (height, diameter, size_of_plate)
        return fiber_object

def assemble_plate(layer_index):
    z_position = layer_index * layer_height
    angle = layer_index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_object = bpy.context.object

    fiber_diameter = layer_height
    spacing = fiber_diameter + fiber_spacing
    total_fibers = max(1, int(size_of_plate / spacing))

    total_space = total_fibers * spacing
    starting_y = -size_of_plate / 2 + spacing / 2 + (size_of_plate - total_space) / 2

    for i in range(total_fibers):
        fiber_center_y = starting_y + i * spacing
        fiber_instance = generate_fiber(
            fiber_form=fiber_form,
            diameter=fiber_diameter,
            x_coord=0,
            y_coord=fiber_center_y,
            z_coord=z_position,
            height=layer_height
        )
        fiber_instance.parent = empty_object
        fiber_instance.matrix_parent_inverse = empty_object.matrix_world.inverted()

    empty_object.rotation_euler[2] = math.radians(angle)
    return empty_object

# Create the helical structure
for layer_index in range(num_layers):
    assemble_plate(layer_index)
