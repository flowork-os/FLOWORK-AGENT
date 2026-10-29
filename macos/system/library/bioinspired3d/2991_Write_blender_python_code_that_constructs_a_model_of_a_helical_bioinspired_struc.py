# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_python_code_that_constructs_a_model_of_a_helical_bioinspired_struc" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender python code that constructs a model of a helical bioinspired structure with flat rectangular struts in each layer

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the fiber arrangement
num_layers = 6  # Total number of layers
angle_increment = 20  # Rotation angle for each layer
fiber_shape_type = 'rect'  # Shape of the fibers

# Overall structure dimensions
final_height = 2.0  # Height of the structure
plate_dimension = 2.0  # Size of each plate
layer_thickness = final_height / num_layers  # Thickness of each layer
fiber_gap = 0.01  # Gap between fibers


def add_fiber(shape, diameter, x, y, z, thickness):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z), rotation=(0, math.radians(90), 0))
        fiber_object = bpy.context.object
        fiber_object.dimensions = (thickness, diameter, plate_dimension)
        return fiber_object


def create_layer(idx):
    z_height = idx * layer_thickness
    rotation_angle = idx * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_height))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_spacing = fiber_diameter + fiber_gap
    total_fibers = max(1, int(plate_dimension / fiber_spacing))

    total_space = total_fibers * fiber_spacing
    start_y = -plate_dimension / 2 + fiber_spacing / 2 + (plate_dimension - total_space) / 2

    for i in range(total_fibers):
        fiber_center_y = start_y + i * fiber_spacing
        fiber_instance = add_fiber(fiber_shape_type, fiber_diameter, 0, fiber_center_y, z_height, layer_thickness)
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Construct the helical structure
for i in range(num_layers):
    create_layer(i)
