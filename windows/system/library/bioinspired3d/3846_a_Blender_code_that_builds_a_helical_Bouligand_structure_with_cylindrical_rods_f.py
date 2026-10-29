# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_that_builds_a_helical_Bouligand_structure_with_cylindrical_rods_f" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code that builds a helical Bouligand structure with cylindrical rods forming each layer Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 12
angle_increment = 10
fiber_type = 'cylinder'

structure_height = 2
square_plate_size = 2
thickness_per_layer = structure_height / layer_count

def add_cylinder(diameter, position):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=diameter / 2,
        depth=square_plate_size,
        location=position,
        rotation=(0, math.radians(90), 0)
    )
    return bpy.context.object

def construct_layer(layer_idx):
    z_position = layer_idx * thickness_per_layer
    rotation_angle = layer_idx * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = thickness_per_layer
    fiber_count = max(1, int(square_plate_size / fiber_diameter))

    total_fiber_length = fiber_count * fiber_diameter
    remaining_space = square_plate_size - total_fiber_length
    start_y_position = -square_plate_size / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_position = start_y_position + i * fiber_diameter
        fiber_instance = add_cylinder(fiber_diameter, (0, fiber_y_position, z_position))
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_y_position, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')

for index in range(layer_count):
    construct_layer(index)
