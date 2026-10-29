# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_to_create_a_helical_twisted_ply_material_made_of_cylindrical_fi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script to create a helical twisted ply material made of cylindrical fibers

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure settings
num_layers = 6  # Number of layers in the structure
rotation_degrees = 12  # Rotation angle for each layer in degrees
fiber_style = 'cylinder'  # Shape of fibers

# Dimensions
total_height = 2  # Overall height of the structure
plate_dimension = 2  # Dimensions of each plate
layer_height = total_height / num_layers  # Height of each layer

def add_fiber_object(style, diameter, x, y, z):
    if style == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object


def create_layer(index):
    # Create a layer of fibers in a helical arrangement
    z_position = index * layer_height
    rotation_angle = index * rotation_degrees

    # Create an empty object for the fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_height
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_space = fiber_count * fiber_diameter
    remaining_space = plate_dimension - total_fiber_space
    initial_y = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_position = initial_y + i * fiber_diameter
        fiber_instance = add_fiber_object(
            style=fiber_style,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y_position,
            z=z_position
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_y_position, 0)

    # Select and activate the empty layer for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_empty

# Generate the helical structure
for i in range(num_layers):
    create_layer(i)
