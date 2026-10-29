# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_making_a_model_of_a_helical_Bouligand_bioinspired_structure_m" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for making a model of a helical Bouligand bioinspired structure made of cylindrical fibers.

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical structure
layer_amount = 5  # Total number of layers
angle_increment = 18  # Rotation angle for each layer
fiber_shape_type = 'cylinder'  # Shape of fibers

# Dimensions
total_structure_height = 2  # Total height of the structure
plate_dimension = 2  # Dimensions of each plate
layer_thickness = total_structure_height / layer_amount  # Thickness of each layer

# Function to create a fiber
def create_fiber(shape, diameter, x, y, z):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

# Function to create a layer
def add_layer(index):
    z_position = index * layer_thickness
    rotation_angle = index * angle_increment

    # Create an empty object to hold fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_space = fiber_count * fiber_diameter
    remaining_space = plate_dimension - total_fiber_space
    start_y = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y = start_y + i * fiber_diameter
        fiber = create_fiber(
            shape=fiber_shape_type,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y,
            z=z_position
        )
        fiber.parent = layer_empty
        fiber.location = (0, fiber_y, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_empty

# Generate the helical structure
for i in range(layer_amount):
    add_layer(i)
