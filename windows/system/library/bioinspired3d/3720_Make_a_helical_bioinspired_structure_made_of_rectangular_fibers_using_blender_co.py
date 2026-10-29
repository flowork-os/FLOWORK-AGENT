# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_helical_bioinspired_structure_made_of_rectangular_fibers_using_blender_co" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a helical bioinspired structure made of rectangular fibers using blender code Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure parameters
layer_count = 12  # Number of layers
rotation_angle = 5  # Angle of rotation for each layer
fiber_form = 'rect'  # Fiber shape

# Dimensions for the structure
height_of_structure = 2.0  # Total height
size_of_plate = 2.0  # Size of each plate
thickness_of_layer = height_of_structure / layer_count  # Layer thickness
spacing_between_fibers = 0.01  # Gap between fibers

def insert_fiber(fiber_form, diameter, x_pos, y_pos, z_pos, thickness):
    if fiber_form == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_pos, y_pos, z_pos), rotation=(0, math.radians(90), 0))
        fiber_obj = bpy.context.object
        fiber_obj.dimensions = (thickness, diameter, size_of_plate)
        return fiber_obj

def layer_creation(layer_index):
    z_position = layer_index * thickness_of_layer
    rotation_offset = layer_index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_radius = thickness_of_layer
    fiber_spacing = fiber_radius + spacing_between_fibers
    fiber_total = max(1, int(size_of_plate / fiber_spacing))

    total_spacing = fiber_total * fiber_spacing
    start_y = -size_of_plate / 2 + fiber_spacing / 2 + (size_of_plate - total_spacing) / 2

    for i in range(fiber_total):
        fiber_y_center = start_y + i * fiber_spacing
        fiber_instance = insert_fiber(fiber_form, fiber_radius, 0, fiber_y_center, z_position, thickness_of_layer)
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_offset)
    return layer_empty

# Generate the structure
for index in range(layer_count):
    layer_creation(index)
