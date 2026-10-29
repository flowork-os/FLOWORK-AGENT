# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_code_construct_a_helical_twisted_ply_bioinspired_material_where_ea" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender code construct a helical twisted ply bioinspired material where each ply consists of cylindrical fibers. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_total = 6  # Total layers in the structure
angle_increment = 25  # Rotation angle for each layer
fiber_shape = 'cylinder'  # Type of fibers

structure_height = 2.0  # Total height of the structure
plate_dimension = 2.0  # Width and length of each plate
layer_thickness = structure_height / layer_total  # Thickness of each layer

def add_fiber_instance(shape, diameter, x_pos, y_pos, z_pos):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def construct_helical_layer(layer_index):
    z_position = layer_index * layer_thickness
    rotation_for_layer = layer_index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_layer = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_space = fiber_count * fiber_diameter
    leftover_space = plate_dimension - total_fiber_space
    start_y = -plate_dimension / 2 + (fiber_diameter / 2) + (leftover_space / 2)

    for i in range(fiber_count):
        fiber_y = start_y + i * fiber_diameter
        fiber_instance = add_fiber_instance(
            shape=fiber_shape,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y,
            z_pos=z_position
        )
        fiber_instance.parent = empty_layer
        fiber_instance.location = (0, fiber_y, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_layer
    empty_layer.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_for_layer),
        orient_axis='Z'
    )

    return empty_layer

for index in range(layer_total):
    construct_helical_layer(index)
