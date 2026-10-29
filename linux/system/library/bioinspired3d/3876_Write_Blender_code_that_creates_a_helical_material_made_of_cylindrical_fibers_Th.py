# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_Blender_code_that_creates_a_helical_material_made_of_cylindrical_fibers_Th" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write Blender code that creates a helical material made of cylindrical fibers Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

ply_count = 12  # Total plies in the structure
rotation_step = 5  # Rotation angle for each ply in degrees
fiber_geometry = 'cylinder'  # Geometry type of fibers

structure_height = 2.0  # Height of the complete structure
plate_dimension = 2.0  # Width and depth of each plate
thickness_per_ply = structure_height / ply_count  # Thickness calculation

def create_fiber_object(geometry, diameter, position):
    if geometry == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=position,
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def generate_ply(index):
    z_position = index * thickness_per_ply
    rotation_angle = index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_object = bpy.context.object

    fiber_diameter = thickness_per_ply
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_length = fiber_count * fiber_diameter
    remaining_space = plate_dimension - total_fiber_length
    starting_y = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_position = starting_y + i * fiber_diameter
        fiber_instance = create_fiber_object(
            geometry=fiber_geometry,
            diameter=fiber_diameter,
            position=(0, fiber_y_position, z_position)
        )
        fiber_instance.parent = empty_object
        fiber_instance.location = (0, fiber_y_position, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_object
    empty_object.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return empty_object

for i in range(ply_count):
    generate_ply(i)
