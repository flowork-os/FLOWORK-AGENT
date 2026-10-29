# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_script_build_a_model_of_a_helical_bioinspired_structure_with" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender script build a model of a helical bioinspired structure with each layer formed by rectangular fibers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure parameters
layer_quantity = 12  # Number of layers in the helical structure
angle_per_layer = 10  # Angle for each layer's rotation
fiber_form = "rect"

# Structure dimensions
total_height = 2  # Complete height of the structure
plate_dimension = 2  # Each plate's width and length
layer_height = total_height / layer_quantity  # Height of each layer
fiber_separation = 0.01  # Space between fibers

def generate_fiber(form, diameter, x, y, z, height):
    if form == "rect":
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        fiber_object = bpy.context.object
        fiber_object.dimensions = (height, diameter, plate_dimension)
        return fiber_object

def create_layer(index):
    # Creates a layer of fibers arranged in a helical format.

    height_position = index * layer_height
    rotation_angle = index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_height
    spacing_between_fibers = fiber_diameter + fiber_separation
    fiber_count = max(1, int(plate_dimension / spacing_between_fibers))

    total_needed_space = fiber_count * spacing_between_fibers
    start_y_coordinate = -plate_dimension / 2 + spacing_between_fibers / 2 + (plate_dimension - total_needed_space) / 2

    for i in range(fiber_count):
        fiber_y_position = start_y_coordinate + i * spacing_between_fibers
        fiber_instance = generate_fiber(
            form=fiber_form,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y_position,
            z=height_position,
            height=layer_height
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Construct the helical structure
for i in range(layer_quantity):
    create_layer(i)
