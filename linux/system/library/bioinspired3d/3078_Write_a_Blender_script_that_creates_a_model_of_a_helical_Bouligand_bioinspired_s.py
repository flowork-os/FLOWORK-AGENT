# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_Blender_script_that_creates_a_model_of_a_helical_Bouligand_bioinspired_s" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a Blender script that creates a model of a helical Bouligand bioinspired structure where each ply consists of cylindrical fibers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 15  # Total number of layers
rotation_angle_step = 3  # Degrees of rotation for each layer
fiber_shape_type = 'cylinder'  # Shape of fibers

structure_total_height = 2.0  # Height of the entire structure
plate_dimension_size = 2.0  # Size of each plate
layer_thickness_value = structure_total_height / layer_count  # Thickness of each layer


def create_fiber_shape(shape_type, diameter, position):
    if shape_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension_size,
            location=position,
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object


def build_layer(layer_index):
    z_coordinate = layer_index * layer_thickness_value
    rotation_angle = layer_index * rotation_angle_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_coordinate))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness_value
    fiber_count = max(1, int(plate_dimension_size / fiber_diameter))

    total_fiber_space = fiber_count * fiber_diameter
    leftover_space = plate_dimension_size - total_fiber_space
    start_y = -plate_dimension_size / 2 + (fiber_diameter / 2) + (leftover_space / 2)

    for i in range(fiber_count):
        fiber_y_position = start_y + i * fiber_diameter
        fiber_object = create_fiber_shape(
            shape_type=fiber_shape_type,
            diameter=fiber_diameter,
            position=(0, fiber_y_position, z_coordinate)
        )
        fiber_object.parent = layer_empty
        fiber_object.location = (0, fiber_y_position, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_empty

for index in range(layer_count):
    build_layer(index)
