# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_a_helical_twisted_ply_bioinspired_material_where_each_ply_consi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of a helical twisted ply bioinspired material where each ply consists of rectangular fibers in blender code Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Number of layers in the structure
angle_increment = 5  # Degrees of rotation for each layer
fiber_type = "rect"  # Type of fiber shape

# Dimensions of the overall structure
structure_height = 2  # Total height of the structure
square_plate_size = 2  # Size of each square plate
layer_thickness = structure_height / layers_count  # Thickness of each layer
spacing_between_fibers = 0.01  # Gap between fibers

def create_fiber(fiber_type, diameter, x_pos, y_pos, z_pos, thickness):
    if fiber_type == "rect":
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, square_plate_size)
        return cube

def build_plate(layer_index):
    height_position = layer_index * layer_thickness
    rotation_angle = layer_index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_position))
    empty_plate = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_spacing = fiber_diameter + spacing_between_fibers
    fiber_count = max(1, int(square_plate_size / fiber_spacing))

    total_fiber_space = fiber_count * fiber_spacing
    start_y_position = -square_plate_size / 2 + fiber_spacing / 2 + (square_plate_size - total_fiber_space) / 2

    for i in range(fiber_count):
        fiber_y_center = start_y_position + i * fiber_spacing
        fiber_instance = create_fiber(
            fiber_type=fiber_type,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_center,
            z_pos=height_position,
            thickness=layer_thickness
        )
        fiber_instance.parent = empty_plate
        fiber_instance.matrix_parent_inverse = empty_plate.matrix_world.inverted()

    empty_plate.rotation_euler[2] = math.radians(rotation_angle)
    return empty_plate

# Construct the entire structure
for layer in range(layers_count):
    build_plate(layer)
