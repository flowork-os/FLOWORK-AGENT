# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_code_that_builds_a_model_of_a_helical_stacked_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender code that builds a model of a helical stacked bioinspired material made of rectangular fibers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Total number of layers in the structure
angle_per_layer = 15  # Degrees of rotation for each layer
fiber_type = 'rectangular'  # Type of fiber shape

# Dimensions of the overall structure
height_of_structure = 2  # Complete height of the structure
plate_dimension = 2  # Width and length of each square plate
layer_thickness = height_of_structure / layers_count  # Thickness of each layer
fiber_spacing = 0.01  # Gap between fibers

def create_fiber(shape, diameter, x, y, z, thickness):
    if shape == 'rectangular':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, plate_dimension)
        return cube


def generate_layer(layer_index):
    # Constructs a helical layer composed of fibers.

    z_position = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    spacing_between_fibers = fiber_diameter + fiber_spacing
    total_fibers = max(1, int(plate_dimension / spacing_between_fibers))

    total_fiber_space = total_fibers * spacing_between_fibers
    start_y_position = -plate_dimension / 2 + spacing_between_fibers / 2 + (plate_dimension - total_fiber_space) / 2

    for j in range(total_fibers):
        fiber_y_center = start_y_position + j * spacing_between_fibers
        fiber_instance = create_fiber(
            shape=fiber_type,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y_center,
            z=z_position,
            thickness=layer_thickness
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Generate the complete structure
for k in range(layers_count):
    generate_layer(k)
