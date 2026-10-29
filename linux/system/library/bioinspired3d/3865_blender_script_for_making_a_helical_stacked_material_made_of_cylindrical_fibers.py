# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_making_a_helical_stacked_material_made_of_cylindrical_fibers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for making a helical stacked material made of cylindrical fibers. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

ply_count = 8  # Number of plies in the structure
angle_increment = 10  # Rotation angle for each ply
fiber_shape_type = 'cylinder'  # Fiber shape type

full_height = 2.0  # Total height of the structure
square_plate_size = 2.0  # Size of each square plate
thickness_per_ply = full_height / ply_count  # Thickness of each ply

def add_fiber_shape(shape_type, diameter, x_coord, y_coord, z_coord, thickness):
    if shape_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=square_plate_size,
            location=(x_coord, y_coord, z_coord),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def generate_plate(plate_index):
    z_offset = plate_index * thickness_per_ply
    rotation_angle = plate_index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_offset))
    empty_object = bpy.context.object

    fiber_diameter = thickness_per_ply
    fiber_quantity = max(1, int(square_plate_size / fiber_diameter))

    total_fiber_area = fiber_quantity * fiber_diameter
    additional_space = square_plate_size - total_fiber_area
    initial_y_coord = -square_plate_size / 2 + (fiber_diameter / 2) + (additional_space / 2)

    for i in range(fiber_quantity):
        fiber_y = initial_y_coord + i * fiber_diameter
        fiber_instance = add_fiber_shape(
            shape_type=fiber_shape_type,
            diameter=fiber_diameter,
            x_coord=0,
            y_coord=fiber_y,
            z_coord=z_offset,
            thickness=thickness_per_ply
        )
        fiber_instance.parent = empty_object
        fiber_instance.location = (0, fiber_y, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_object
    empty_object.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return empty_object

for index in range(ply_count):
    generate_plate(index)
