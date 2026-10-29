# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_a_helical_Bouligand_bioinspired_material_with_flat_rectangu" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of a helical Bouligand bioinspired material with flat rectangular struts in each layer in python blender code

import bpy
import math

# Clean the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
num_layers = 12  # Total layers of fibers
angle_increment = 5  # Rotation angle for each layer
fiber_shape_type = 'rect'  # Shape of fibers

# Dimensions of the structure
full_height = 2  # Height of the complete structure
square_plate_size = 2  # Each plate's width and length
layer_height = full_height / num_layers  # Height of each layer
spacing_between_fibers = 0.01  # Gap between fibers


def create_fiber_shape(shape_type, diameter, x, y, z, height):
    if shape_type == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        fiber_cube = bpy.context.object
        fiber_cube.dimensions = (height, diameter, square_plate_size)
        return fiber_cube


def build_layer(index):
    # Builds a helical layer of fibers.

    z_position = index * layer_height
    rotation_angle = index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty_object = bpy.context.object

    fiber_diameter = layer_height
    fiber_distance = fiber_diameter + spacing_between_fibers
    total_fiber_count = max(1, int(square_plate_size / fiber_distance))

    total_fiber_space = total_fiber_count * fiber_distance
    start_y_position = -square_plate_size / 2 + fiber_distance / 2 + (square_plate_size - total_fiber_space) / 2

    for i in range(total_fiber_count):
        fiber_y_center = start_y_position + i * fiber_distance
        fiber_instance = create_fiber_shape(
            shape_type=fiber_shape_type,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y_center,
            z=z_position,
            height=layer_height
        )
        fiber_instance.parent = layer_empty_object
        fiber_instance.matrix_parent_inverse = layer_empty_object.matrix_world.inverted()

    layer_empty_object.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty_object

# Construct the full structure
for i in range(num_layers):
    build_layer(i)
