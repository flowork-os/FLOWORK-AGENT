# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_that_makes_a_helical_bioinspired_material_with_cylindrical_rods_for" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code that makes a helical bioinspired material with cylindrical rods forming each layer. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

ply_total = 8  # Number of plies
rotation_degrees = 20  # Degrees of rotation for each ply
fiber_geom = 'cylinder'  # Shape of the fibers

overall_height = 2  # Total height of the structure
square_plate_size = 2  # Width and length of each square plate
thickness_per_ply = overall_height / ply_total  # Thickness of each ply

def insert_fiber(geometry, diameter, x_pos, y_pos, z_pos):
    if geometry == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=square_plate_size,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def create_helical_layer(index):
    z_coord = index * thickness_per_ply
    rotation_amount = index * rotation_degrees

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_coord))
    layer_empty_object = bpy.context.object

    fiber_diameter = thickness_per_ply
    fiber_quantity = max(1, int(square_plate_size / fiber_diameter))

    total_fiber_length = fiber_quantity * fiber_diameter
    space_remaining = square_plate_size - total_fiber_length
    start_position_y = -square_plate_size / 2 + (fiber_diameter / 2) + (space_remaining / 2)

    for j in range(fiber_quantity):
        fiber_y_position = start_position_y + j * fiber_diameter
        fiber_instance = insert_fiber(
            geometry=fiber_geom,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_position,
            z_pos=z_coord
        )
        fiber_instance.parent = layer_empty_object
        fiber_instance.location = (0, fiber_y_position, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty_object
    layer_empty_object.select_set(True)
    bpy.ops.transform.rotate(
        value=math.radians(rotation_amount),
        orient_axis='Z'
    )
    return layer_empty_object

for layer_index in range(ply_total):
    create_helical_layer(layer_index)
