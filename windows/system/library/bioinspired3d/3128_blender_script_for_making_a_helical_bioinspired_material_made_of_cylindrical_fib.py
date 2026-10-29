# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_making_a_helical_bioinspired_material_made_of_cylindrical_fib" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for making a helical bioinspired material made of cylindrical fibers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
layers = 8  # Number of layers in the helical structure
rotation_angle = 10  # Rotation angle for each layer in degrees
fiber_form = 'cylinder'  # Shape of the fibers

# Structure dimensions
structure_height = 2  # Total height of the structure
plate_length = 2  # Length of each plate
layer_height = structure_height / layers  # Height of each layer

def add_cylinder(shape, diameter, x, y, z, height):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_length,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object


def construct_layer(layer_index):
    # Constructs a layer of fibers in a helical pattern.
    z_position = layer_index * layer_height
    angle = layer_index * rotation_angle

    # Create an empty object to hold the fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_radius = layer_height
    fiber_count = max(1, int(plate_length / fiber_radius))

    total_fiber_space = fiber_count * fiber_radius
    extra_space = plate_length - total_fiber_space
    start_y = -plate_length / 2 + (fiber_radius / 2) + (extra_space / 2)

    for i in range(fiber_count):
        fiber_y = start_y + i * fiber_radius
        fiber_object = add_cylinder(
            shape=fiber_form,
            diameter=fiber_radius,
            x=0,
            y=fiber_y,
            z=z_position,
            height=layer_height
        )
        fiber_object.parent = layer_empty
        fiber_object.location = (0, fiber_y, 0)

    # Select and activate the empty layer for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(angle),
        orient_axis='Z'
    )

    return layer_empty

# Generate the helical structure
for index in range(layers):
    construct_layer(index)
