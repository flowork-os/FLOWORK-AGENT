# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_to_construct_a_helical_twisted_ply_bioinspired_structure_made_of_cy" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code to construct a helical twisted ply bioinspired structure made of cylindrical fibers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Total number of layers
angle_per_layer = 5  # Degrees of rotation for each layer
fiber_type = 'cylinder'  # Type of fiber shape

# Dimensions of the overall structure
structure_height = 2  # Height of the entire structure
plate_dimension = 2  # Length and width of each plate
layer_thickness = structure_height / layers_count  # Thickness of each layer

def create_fiber(shape, diameter, x_pos, y_pos, z_pos):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object


def construct_layer(layer_index):
    z_position = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    # Create an empty object for the layer
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_size = fiber_count * fiber_diameter
    remaining_space = plate_dimension - total_fiber_size
    start_y_position = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_center = start_y_position + i * fiber_diameter
        fiber_instance = create_fiber(
            shape=fiber_type,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_center,
            z_pos=z_position
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_y_center, 0)

    # Prepare the empty object for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_empty

# Create the entire structure
for index in range(layers_count):
    construct_layer(index)
