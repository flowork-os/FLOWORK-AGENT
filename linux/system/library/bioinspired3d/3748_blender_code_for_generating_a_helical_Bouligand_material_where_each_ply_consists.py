# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_for_generating_a_helical_Bouligand_material_where_each_ply_consists" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code for generating a helical Bouligand material where each ply consists of rectangular fibers Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Number of layers in the design
angle_per_layer = 15  # Degrees of rotation per layer
fiber_type = 'rectangle'  # Type of fiber shape

# Dimensions of the structure
structure_height = 2  # Total height of the structure
plate_dimension = 2  # Size of each plate
layer_thickness = structure_height / layers_count  # Thickness of each layer
fiber_spacing = 0.01  # Gap between fibers


def create_fiber(type_of_fiber, diameter, x_pos, y_pos, z_pos, thickness):
    if type_of_fiber == 'rectangle':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        fiber = bpy.context.object
        fiber.dimensions = (thickness, diameter, plate_dimension)
        return fiber


def generate_layer(layer_index):
    # Generate a layer of fibers in a helical arrangement.

    z_position = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    spacing_between_fibers = fiber_diameter + fiber_spacing
    total_fibers = max(1, int(plate_dimension / spacing_between_fibers))

    total_fiber_space = total_fibers * spacing_between_fibers
    initial_y = -plate_dimension / 2 + spacing_between_fibers / 2 + (plate_dimension - total_fiber_space) / 2

    for i in range(total_fibers):
        fiber_y_center = initial_y + i * spacing_between_fibers
        fiber_object = create_fiber(
            type_of_fiber=fiber_type,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_center,
            z_pos=z_position,
            thickness=layer_thickness
        )
        fiber_object.parent = layer_empty
        fiber_object.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Build the structure
for index in range(layers_count):
    generate_layer(index)
