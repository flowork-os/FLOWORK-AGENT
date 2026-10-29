# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_code__generate_a_helical_twisted_ply_structure_made_of_rectangular" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender code, generate a helical twisted ply structure made of rectangular fibers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Total number of layers in the structure
angle_increment = 5  # Degrees of rotation for each layer
fiber_type = 'rectangular'  # Type of fiber shape

# Dimensions of the entire structure
structure_height = 2.0  # Final height of the structure
plate_dimension = 2.0  # Length and width of each square plate
layer_thickness = structure_height / layers_count  # Thickness of each layer
fiber_spacing = 0.01  # Gap between fibers

def create_fiber(shape, diameter, x_pos, y_pos, z_pos, thickness):
    if shape == 'rectangular':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        new_fiber = bpy.context.object
        new_fiber.dimensions = (thickness, diameter, plate_dimension)
        return new_fiber


def build_layer(layer_index):
    # Constructs a helical layer of fibers
    current_height = layer_index * layer_thickness
    rotation_angle = layer_index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, current_height))
    empty_layer = bpy.context.object

    fiber_diameter = layer_thickness
    spacing_between_fibers = fiber_diameter + fiber_spacing
    total_fibers = max(1, int(plate_dimension / spacing_between_fibers))

    total_fiber_space = total_fibers * spacing_between_fibers
    initial_y = -plate_dimension / 2 + spacing_between_fibers / 2 + (plate_dimension - total_fiber_space) / 2

    for j in range(total_fibers):
        fiber_y_position = initial_y + j * spacing_between_fibers
        fiber_instance = create_fiber(
            shape=fiber_type,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_position,
            z_pos=current_height,
            thickness=layer_thickness
        )
        fiber_instance.parent = empty_layer
        fiber_instance.matrix_parent_inverse = empty_layer.matrix_world.inverted()

    empty_layer.rotation_euler[2] = math.radians(rotation_angle)
    return empty_layer

# Generate the entire structure
for k in range(layers_count):
    build_layer(k)
