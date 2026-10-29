# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_Blender_code__generate_a_helical_Bouligand_bioinspired_material_with_flat" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a Blender code, generate a helical Bouligand bioinspired material with flat rectangular struts in each layer.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure parameters
layer_count = 12  # Number of layers in the helical structure
rotation_angle = 10  # Rotation degree for each layer
fiber_shape_type = 'rect'

# Dimensions of the structure
complete_height = 2.0  # Height of the entire structure
plate_dim = 2.0  # Dimensions of each plate
thickness_of_each_layer = complete_height / layer_count  # Layer thickness
spacing_between_fibers = 0.01  # Gap between fibers

def create_fiber_shape(shape_type, diameter, position):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=position, rotation=(0, math.radians(90), 0))
    fiber = bpy.context.object
    fiber.dimensions = (thickness_of_each_layer, diameter, plate_dim)
    return fiber


def build_layer(layer_index):
    z_position = layer_index * thickness_of_each_layer
    rotation_for_layer = layer_index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = thickness_of_each_layer
    fiber_gap = fiber_diameter + spacing_between_fibers
    fiber_count = max(1, int(plate_dim / fiber_gap))

    total_fiber_space = fiber_count * fiber_gap
    start_y_position = -plate_dim / 2 + fiber_gap / 2 + (plate_dim - total_fiber_space) / 2

    for i in range(fiber_count):
        fiber_center_y = start_y_position + i * fiber_gap
        fiber_instance = create_fiber_shape(
            shape_type=fiber_shape_type,
            diameter=fiber_diameter,
            position=(0, fiber_center_y, z_position)
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_for_layer)
    return layer_empty

# Construct the helical structure
for i in range(layer_count):
    build_layer(i)
