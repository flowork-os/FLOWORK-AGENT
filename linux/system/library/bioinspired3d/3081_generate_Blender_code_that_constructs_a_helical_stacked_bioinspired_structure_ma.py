# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_that_constructs_a_helical_stacked_bioinspired_structure_ma" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code that constructs a helical stacked bioinspired structure made of cylindrical fibers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber arrangement
layer_count = 12  # Total number of layers
rotation_angle = 10  # Degrees of rotation for each layer
fiber_style = 'cylinder'  # Shape of fibers

# Overall dimensions of the structure
height_of_structure = 2.0  # Total height
plate_dimension = 2.0  # Width and length of each plate
thickness_of_layer = height_of_structure / layer_count  # Thickness of each layer

def create_fiber_object(style, diameter, x_pos, y_pos, z_pos):
    if style == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def build_layer(layer_index):
    # Function to create each layer of fibers
    z_position = layer_index * thickness_of_layer
    rotation_value = layer_index * rotation_angle

    # Create an empty object for this layer
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = thickness_of_layer
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    total_space_needed = fiber_count * fiber_diameter
    remaining_space = plate_dimension - total_space_needed
    initial_y = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_position = initial_y + i * fiber_diameter
        fiber_instance = create_fiber_object(
            style=fiber_style,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_position,
            z_pos=z_position
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_y_position, 0)

    # Select the layer empty object and apply rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_value),
        orient_axis='Z'
    )

    return layer_empty

# Generate the helical structure
for i in range(layer_count):
    build_layer(i)
