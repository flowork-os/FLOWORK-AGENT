# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_that_makes_a_model_of_a_helical_twisted_ply_material_made_of_cylind" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code that makes a model of a helical twisted ply material made of cylindrical fibers

import bpy
import math

# Clear existing objects in the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set up parameters for the helical fiber arrangement
num_layers = 7  # Number of layers in the helical structure
rotation_angle = 10  # Rotation for each layer in degrees
fiber_shape = 'cylinder'  # Shape of the fibers

# Define dimensions for the entire structure
height_of_structure = 2.0  # Total height of the structure
plate_dimensions = 2.0  # Size of each square plate
thickness_of_layer = height_of_structure / num_layers  # Thickness for each layer


def add_single_fiber(shape, diameter, x_coord, y_coord, z_coord, thickness):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimensions,
            location=(x_coord, y_coord, z_coord),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object


def create_helical_layer(layer_index):
    # Generates a helical layer composed of fibers.
    z_position = layer_index * thickness_of_layer
    rotation_for_layer = layer_index * rotation_angle

    # Create a parent object for this layer
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_parent = bpy.context.object

    fiber_diameter = thickness_of_layer
    number_of_fibers = max(1, int(plate_dimensions / fiber_diameter))

    total_fiber_area = number_of_fibers * fiber_diameter
    spare_area = plate_dimensions - total_fiber_area
    initial_y_position = -plate_dimensions / 2 + (fiber_diameter / 2) + (spare_area / 2)

    for i in range(number_of_fibers):
        fiber_y_position = initial_y_position + i * fiber_diameter
        fiber_instance = add_single_fiber(
            shape=fiber_shape,
            diameter=fiber_diameter,
            x_coord=0,
            y_coord=fiber_y_position,
            z_coord=z_position,
            thickness=thickness_of_layer
        )
        fiber_instance.parent = layer_parent
        fiber_instance.location = (0, fiber_y_position, 0)

    # Set the layer_parent as the active object before rotating
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_parent
    layer_parent.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_for_layer),
        orient_axis='Z'
    )

    return layer_parent

# Construct the helical structure
for layer in range(num_layers):
    create_helical_layer(layer)
