# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_to_create_a_model_of_a_helical_twisted_ply_bioinspired_structure_wh" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code to create a model of a helical twisted ply bioinspired structure where each ply consists of cylindrical fibers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure parameters
num_layers = 7  # Number of layers in the helical structure
rotation_angle = 10  # Rotation in degrees per layer
fiber_style = 'cylinder'  # Fiber shape type

# Overall dimensions
total_height = 2  # Height of the structure
plate_dim = 2  # Size of each plate
layer_height = total_height / num_layers  # Height of each layer


def add_cylinder(shape, diameter, x_loc, y_loc, z_loc):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dim,
            location=(x_loc, y_loc, z_loc),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object


def generate_layer(index):
    # Generates a helical layer of fibers.
    z_coord = index * layer_height
    rotation_value = index * rotation_angle

    # Create an empty parent object
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_coord))
    empty_layer = bpy.context.object

    fiber_radius = layer_height
    fiber_quantity = max(1, int(plate_dim / fiber_radius))

    total_space = fiber_quantity * fiber_radius
    space_left = plate_dim - total_space
    initial_y = -plate_dim / 2 + (fiber_radius / 2) + (space_left / 2)

    for i in range(fiber_quantity):
        fiber_y_coord = initial_y + i * fiber_radius
        fiber_object = add_cylinder(
            shape=fiber_style,
            diameter=fiber_radius,
            x_loc=0,
            y_loc=fiber_y_coord,
            z_loc=z_coord
        )
        fiber_object.parent = empty_layer
        fiber_object.location = (0, fiber_y_coord, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_layer
    empty_layer.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_value),
        orient_axis='Z'
    )

    return empty_layer

# Create the structure
for i in range(num_layers):
    generate_layer(i)
