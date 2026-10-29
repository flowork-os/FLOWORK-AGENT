# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_to_make_a_helical_twisted_ply_bioinspired_material_where_each_p" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script to make a helical twisted ply bioinspired material where each ply consists of rectangular fibers Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for constructing a helical fiber structure
num_layers = 10  # Total number of layers
angle_per_layer = 15  # Degrees of rotation for each layer
fiber_type = 'rect'

# Dimensions for the overall structure
height_of_structure = 2  # Overall height of the structure
plate_dimension = 2  # Size of each square plate
layer_thickness = height_of_structure / num_layers  # Thickness for each layer
spacing_between_fibers = 0.01  # Gap between fibers

def create_fiber(fiber_type, diameter, x_pos, y_pos, z_pos, thickness):
    if fiber_type == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_pos, y_pos, z_pos), rotation=(0, math.radians(90), 0))
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, plate_dimension)
        return cube

def generate_plate(layer_index):
    z_position = layer_index * layer_thickness
    layer_rotation = layer_index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_plate = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_distance = fiber_diameter + spacing_between_fibers
    total_fibers = max(1, int(plate_dimension / fiber_distance))

    available_space = total_fibers * fiber_distance
    start_y_position = -plate_dimension / 2 + fiber_distance / 2 + (plate_dimension - available_space) / 2

    for i in range(total_fibers):
        fiber_y_center = start_y_position + i * fiber_distance
        fiber_instance = create_fiber(fiber_type=fiber_type, diameter=fiber_diameter, x_pos=0, y_pos=fiber_y_center, z_pos=z_position, thickness=layer_thickness)
        fiber_instance.parent = empty_plate
        fiber_instance.matrix_parent_inverse = empty_plate.matrix_world.inverted()

    empty_plate.rotation_euler[2] = math.radians(layer_rotation)
    return empty_plate

# Construct the full helical structure
for layer in range(num_layers):
    generate_plate(layer)
