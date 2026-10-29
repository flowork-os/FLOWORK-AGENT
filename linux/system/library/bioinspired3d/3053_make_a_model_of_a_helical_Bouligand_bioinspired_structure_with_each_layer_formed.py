# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_a_helical_Bouligand_bioinspired_structure_with_each_layer_formed" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of a helical Bouligand bioinspired structure with each layer formed by rectangular fibers in blender python code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layer_count = 10  # Total number of layers in the structure
angle_increment = 5  # Degrees of rotation for each layer
fiber_type = "rect"  # Type of fiber shape

# Dimensions of the structure
structure_height = 2  # Overall height of the structure
plate_dimension = 2  # Width and length of each plate
layer_thickness = structure_height / layer_count  # Thickness calculation for each layer
fiber_spacing = 0.01  # Gap between fibers

def create_fiber(fiber_type, diameter, x, y, z, thickness):
    if fiber_type == "rect":
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, plate_dimension)
        return cube

def generate_layer(index):
    # Function to generate a layer of fibers in a helical arrangement.

    height_pos = index * layer_thickness
    rotation_angle = index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_pos))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    spacing_between_fibers = fiber_diameter + fiber_spacing
    fiber_count = max(1, int(plate_dimension / spacing_between_fibers))

    total_fiber_space = fiber_count * spacing_between_fibers
    start_y_position = -plate_dimension / 2 + spacing_between_fibers / 2 + (plate_dimension - total_fiber_space) / 2

    for i in range(fiber_count):
        fiber_y_position = start_y_position + i * spacing_between_fibers
        fiber_instance = create_fiber(
            fiber_type=fiber_type,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y_position,
            z=height_pos,
            thickness=layer_thickness
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Building the structure
for i in range(layer_count):
    generate_layer(i)
