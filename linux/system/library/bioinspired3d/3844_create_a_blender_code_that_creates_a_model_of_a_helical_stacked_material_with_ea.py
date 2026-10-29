# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_blender_code_that_creates_a_model_of_a_helical_stacked_material_with_ea" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a blender code that creates a model of a helical stacked material with each layer composed of aligned cylinders think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Number of layers in the structure
angle_per_layer = 5  # Rotation angle in degrees for each layer
fiber_type = 'cylinder'  # Shape of fibers

# Dimensions for the structure
height_total = 2  # Total height of the structure
plate_dimension = 2  # Width and length of each square plate
layer_thickness = height_total / layers_count  # Thickness of each layer

def create_fiber(fiber_type, diameter, x_pos, y_pos, z_pos):
    if fiber_type == 'cylinder':
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
    empty_layer = bpy.context.object

    fiber_radius = layer_thickness
    fiber_count = max(1, int(plate_dimension / fiber_radius))

    total_fiber_length = fiber_count * fiber_radius
    remaining_space = plate_dimension - total_fiber_length
    start_y_position = -plate_dimension / 2 + (fiber_radius / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_position = start_y_position + i * fiber_radius
        fiber_instance = create_fiber(
            fiber_type=fiber_type,
            diameter=fiber_radius,
            x_pos=0,
            y_pos=fiber_y_position,
            z_pos=z_position
        )
        fiber_instance.parent = empty_layer
        fiber_instance.location = (0, fiber_y_position, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_layer
    empty_layer.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return empty_layer

# Create the entire structure
for layer in range(layers_count):
    build_layer(layer)
