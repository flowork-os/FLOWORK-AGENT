# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_code_build_a_helical_Bouligand_bioinspired_material_with_cylindri" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender code build a helical Bouligand bioinspired material with cylindrical rods forming each layer.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
plies = 10  # Number of plies in the design
rotation_angle = 5  # Rotation angle for each ply in degrees
fiber_shape = 'cylinder'  # Shape of the fibers

# Overall structure dimensions
height = 2
plate_dimension = 2
thickness_per_ply = height / plies  # Calculate thickness for each ply


def add_cylinder(fiber_shape, diameter, position):
    if fiber_shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=position,
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object


def create_helical_ply(index):
    # Function to create a helical ply of fibers.
    z_offset = index * thickness_per_ply
    rotation_amount = index * rotation_angle

    # Create an empty object to hold fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_offset))
    empty_object = bpy.context.object

    fiber_diameter = thickness_per_ply
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_length = fiber_count * fiber_diameter
    remaining_space = plate_dimension - total_fiber_length
    start_y = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_position = start_y + i * fiber_diameter
        fiber_instance = add_cylinder(
            fiber_shape=fiber_shape,
            diameter=fiber_diameter,
            position=(0, fiber_y_position, z_offset)
        )
        fiber_instance.parent = empty_object
        fiber_instance.location = (0, fiber_y_position, 0)

    # Deselect all and activate the empty object before rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_object
    empty_object.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_amount),
        orient_axis='Z'
    )

    return empty_object

# Construct the helical structure
for i in range(plies):
    create_helical_ply(i)
