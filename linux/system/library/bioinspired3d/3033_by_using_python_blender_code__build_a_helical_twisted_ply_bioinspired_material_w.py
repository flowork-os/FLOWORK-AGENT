# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_python_blender_code__build_a_helical_twisted_ply_bioinspired_material_w" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using python blender code, build a helical twisted ply bioinspired material where each ply consists of rectangular fibers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Total number of layers
angle_per_layer = 15  # Rotation angle for each layer
fiber_type = "rect"  # Type of fiber shape

# Dimensions of the overall structure
structure_height = 2  # Total height of the structure
plate_dimension = 2  # Dimension of each square plate
layer_thickness = structure_height / layers_count  # Thickness of each layer
fiber_spacing_gap = 0.01  # Gap between fibers

def create_fiber(shape_type, diameter, x_pos, y_pos, z_pos, thickness):
    if shape_type == "rect":
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

    height_offset = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_offset))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_distance = fiber_diameter + fiber_spacing_gap
    fiber_count = max(1, int(plate_dimension / fiber_distance))

    total_length = fiber_count * fiber_distance
    start_y_position = -plate_dimension / 2 + fiber_distance / 2 + (plate_dimension - total_length) / 2

    for i in range(fiber_count):
        fiber_y_center = start_y_position + i * fiber_distance
        fiber_instance = create_fiber(
            shape_type=fiber_type,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_center,
            z_pos=height_offset,
            thickness=layer_thickness
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Construct the helical structure
for j in range(layers_count):
    generate_layer(j)
