# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_Python_script_create_a_helical_Bouligand_bioinspired_material_w" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender Python script create a helical Bouligand bioinspired material with each layer formed by rectangular fibers think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Total number of layers
angle_per_layer = 5  # Degrees of rotation per layer
fiber_type = 'rect'

# Dimensions for the entire structure
structure_height = 2.0  # Overall height
square_plate_size = 2.0  # Size of each plate
layer_thickness = structure_height / layers_count  # Thickness per layer
fiber_spacing = 0.01  # Gap between fibers

def create_fiber(fiber_type, diameter, x_pos, y_pos, z_pos, thickness):
    if fiber_type == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_pos, y_pos, z_pos), rotation=(0, math.radians(90), 0))
        fiber = bpy.context.object
        fiber.dimensions = (thickness, diameter, square_plate_size)
        return fiber

def generate_layer(layer_index):
    height_position = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    spacing_between_fibers = fiber_diameter + fiber_spacing
    fiber_count = max(1, int(square_plate_size / spacing_between_fibers))

    total_fiber_space = fiber_count * spacing_between_fibers
    start_y_position = -square_plate_size / 2 + spacing_between_fibers / 2 + (square_plate_size - total_fiber_space) / 2

    for i in range(fiber_count):
        fiber_y_position = start_y_position + i * spacing_between_fibers
        fiber_object = create_fiber(fiber_type=fiber_type, diameter=fiber_diameter, x_pos=0, y_pos=fiber_y_position, z_pos=height_position, thickness=layer_thickness)
        fiber_object.parent = layer_empty
        fiber_object.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Build the helical structure
for index in range(layers_count):
    generate_layer(index)
