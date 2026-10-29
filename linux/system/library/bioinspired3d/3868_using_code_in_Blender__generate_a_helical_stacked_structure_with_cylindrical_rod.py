# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_code_in_Blender__generate_a_helical_stacked_structure_with_cylindrical_rod" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using code in Blender, generate a helical stacked structure with cylindrical rods forming each layer Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_amount = 7  # Number of layers in the structure
rotation_degree = 12  # Rotation angle for each layer
fiber_type = 'cylinder'  # Type of fiber shape

height_of_structure = 2.0  # Total height of the structure
plate_measure = 2.0  # Width and length of each plate
layer_thickness = height_of_structure / layer_amount  # Thickness of each layer

def add_fiber_object(fiber_shape, diameter, x_pos, y_pos, z_pos):
    if fiber_shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_measure,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def construct_layer(layer_index):
    z_position = layer_index * layer_thickness
    rotation_angle = layer_index * rotation_degree

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_count = max(1, int(plate_measure / fiber_diameter))

    total_fiber_space = fiber_count * fiber_diameter
    remaining_space = plate_measure - total_fiber_space
    starting_y = -plate_measure / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_position = starting_y + i * fiber_diameter
        fiber_instance = add_fiber_object(
            fiber_shape=fiber_type,
            diameter=fiber_diameter,
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

for index in range(layer_amount):
    construct_layer(index)
