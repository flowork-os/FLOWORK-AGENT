# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_helical_twisted_ply_material_with_each_layer_formed_by_rectangular_fibe" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a helical twisted ply material with each layer formed by rectangular fibers in code in Blender

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure parameters
layers_count = 7  # Number of layers in the structure
layer_rotation_angle = 10  # Rotation angle for each layer
fiber_form = 'rect'  # Shape of fibers

# Structure dimensions
structure_height = 2  # Total height of the structure
square_plate_size = 2  # Size of each plate
layer_height = structure_height / layers_count  # Height of each layer
fiber_separation = 0.01  # Gap between fibers


def insert_fiber(shape, diameter, x, y, z, height):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z), rotation=(0, math.radians(90), 0))
        cube = bpy.context.object
        cube.dimensions = (height, diameter, square_plate_size)
        return cube


def assemble_plate(index):
    # Assembles a plate with fibers in a helical orientation
    z_position = index * layer_height
    rotation_angle = index * layer_rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_object = bpy.context.object

    fiber_diameter = layer_height
    fiber_spacing = fiber_diameter + fiber_separation
    fiber_count = max(1, int(square_plate_size / fiber_spacing))

    total_fiber_space = fiber_count * fiber_spacing
    initial_y = -square_plate_size / 2 + fiber_spacing / 2 + (square_plate_size - total_fiber_space) / 2

    for i in range(fiber_count):
        fiber_y_position = initial_y + i * fiber_spacing
        fiber_instance = insert_fiber(shape=fiber_form, diameter=fiber_diameter, x=0, y=fiber_y_position, z=z_position, height=layer_height)
        fiber_instance.parent = empty_object
        fiber_instance.matrix_parent_inverse = empty_object.matrix_world.inverted()

    empty_object.rotation_euler[2] = math.radians(rotation_angle)
    return empty_object

# Generate the helical structure
for i in range(layers_count):
    assemble_plate(i)
