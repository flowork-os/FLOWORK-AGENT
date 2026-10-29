# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_code__create_a_helical_stacked_bioinspired_material_made_of_rectan" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender code, create a helical stacked bioinspired material made of rectangular fibers

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
layers = 9
rotation_step = 8
fiber_style = 'rect'

# Structure dimensions
height_of_structure = 2.0
plate_dimension = 2.0
layer_height = height_of_structure / layers
fiber_spacing = 0.01

# Helper function to create fibers
def create_fiber(shape, diameter, x, y, z, height):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z), rotation=(0, math.radians(90), 0))
        fiber = bpy.context.object
        fiber.dimensions = (height, diameter, plate_dimension)
        return fiber

# Function to generate a layer of fibers
def generate_layer(layer_index):
    z_position = layer_index * layer_height
    rotation_angle = layer_index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_layer = bpy.context.object

    fiber_diameter = layer_height
    spacing_between_fibers = fiber_diameter + fiber_spacing
    fiber_count = max(1, int(plate_dimension / spacing_between_fibers))

    total_spacing = fiber_count * spacing_between_fibers
    initial_y_position = -plate_dimension / 2 + spacing_between_fibers / 2 + (plate_dimension - total_spacing) / 2

    for i in range(fiber_count):
        fiber_y_position = initial_y_position + i * spacing_between_fibers
        fiber_instance = create_fiber(shape=fiber_style, diameter=fiber_diameter, x=0, y=fiber_y_position, z=z_position, height=layer_height)
        fiber_instance.parent = empty_layer
        fiber_instance.matrix_parent_inverse = empty_layer.matrix_world.inverted()

    empty_layer.rotation_euler[2] = math.radians(rotation_angle)
    return empty_layer

# Build the entire helical structure
for i in range(layers):
    generate_layer(i)
