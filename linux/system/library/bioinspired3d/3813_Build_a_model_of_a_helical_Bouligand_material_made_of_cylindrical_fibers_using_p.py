# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_a_helical_Bouligand_material_made_of_cylindrical_fibers_using_p" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of a helical Bouligand material made of cylindrical fibers using python blender code think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

ply_count = 10  # Total number of layers
angle_per_ply = 5  # Degrees of rotation for each layer
fiber_type = 'cylinder'  # Type of fiber used

structure_height = 2.0  # Height of the entire structure
plate_dimension = 2.0  # Dimensions of each plate
thickness_per_ply = structure_height / ply_count  # Thickness calculation

def create_fiber(shape, diameter, x, y, z):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def build_plate(plate_index):
    z_position = plate_index * thickness_per_ply
    rotation_angle = plate_index * angle_per_ply

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_plate = bpy.context.object

    fiber_diameter = thickness_per_ply
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_length = fiber_count * fiber_diameter
    remaining_space = plate_dimension - total_fiber_length
    start_position_y = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_position = start_position_y + i * fiber_diameter
        fiber_object = create_fiber(
            shape=fiber_type,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y_position,
            z=z_position
        )
        fiber_object.parent = empty_plate
        fiber_object.location = (0, fiber_y_position, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_plate
    empty_plate.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return empty_plate

for index in range(ply_count):
    build_plate(index)
