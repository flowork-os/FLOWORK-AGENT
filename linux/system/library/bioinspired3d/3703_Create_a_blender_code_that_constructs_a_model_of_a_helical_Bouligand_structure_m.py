# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_blender_code_that_constructs_a_model_of_a_helical_Bouligand_structure_m" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a blender code that constructs a model of a helical Bouligand structure made of rectangular fibers. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Total layers in the helical structure
angle_per_layer = 15  # Degrees of rotation for each layer
fiber_style = 'rect'  # Shape of the fibers

# Dimensions of the overall structure
structure_height = 2.0  # Height of the complete structure
plate_dimension = 2.0  # Dimension of each square plate
layer_thickness = structure_height / layers_count  # Thickness of each layer
fiber_spacing = 0.01  # Gap between fibers

def create_fiber(style, diameter, x_pos, y_pos, z_pos, thickness):
    if style == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, plate_dimension)
        return cube

def generate_layer(layer_index):
    height_offset = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_offset))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    spacing_between_fibers = fiber_diameter + fiber_spacing
    fiber_count = max(1, int(plate_dimension / spacing_between_fibers))

    total_spacing = fiber_count * spacing_between_fibers
    initial_y = -plate_dimension / 2 + spacing_between_fibers / 2 + (plate_dimension - total_spacing) / 2

    for i in range(fiber_count):
        fiber_y_position = initial_y + i * spacing_between_fibers
        fiber_object = create_fiber(
            style=fiber_style,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_position,
            z_pos=height_offset,
            thickness=layer_thickness
        )
        fiber_object.parent = layer_empty
        fiber_object.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Build the entire structure
for index in range(layers_count):
    generate_layer(index)
