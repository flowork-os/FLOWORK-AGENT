# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_a_helical_stacked_bioinspired_structure_with_each_layer_composed" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of a helical stacked bioinspired structure with each layer composed of aligned cylinders using code in Blender Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Total number of layers
angle_per_layer = 5  # Degrees of rotation for each layer
fiber_type = 'cylinder'  # Type of fiber shape

# Dimensions of the overall structure
height_total = 2  # Overall height of the structure
plate_dimension = 2  # Dimensions of each square plate
layer_thickness = height_total / layers_count  # Thickness per layer

def create_fiber(shape, diameter, x_pos, y_pos, z_pos):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def build_layer(layer_index):
    z_position = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_radius = layer_thickness
    number_of_fibers = max(1, int(plate_dimension / fiber_radius))

    total_fiber_length = number_of_fibers * fiber_radius
    remaining_space = plate_dimension - total_fiber_length
    initial_y = -plate_dimension / 2 + (fiber_radius / 2) + (remaining_space / 2)

    for j in range(number_of_fibers):
        fiber_y_position = initial_y + j * fiber_radius
        fiber_instance = create_fiber(
            shape=fiber_type,
            diameter=fiber_radius,
            x_pos=0,
            y_pos=fiber_y_position,
            z_pos=z_position
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_y_position, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)
    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )
    return layer_empty

# Create the entire structure
for k in range(layers_count):
    build_layer(k)
