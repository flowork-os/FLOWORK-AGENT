# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_helical_material_where_each_ply_consists_of_cylindrical_fibers_in_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a helical material where each ply consists of cylindrical fibers in blender python code

import bpy
import math

# Clear the Blender scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
ply_count = 6  # Total number of plies
rotation_angle = 20  # Degrees of rotation for each successive ply
fiber_type = 'cylinder'  # Shape of fibers

# Dimensions of the overall structure
structure_height = 2.0  # Total height of the structure
plate_size = 2.0  # Width and length of each square plate
ply_thickness = structure_height / ply_count  # Thickness of each ply


def place_fiber(fiber_type, diameter, x_pos, y_pos, z_pos):
    if fiber_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_size,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object


def form_layer(index):
    # Creates a helical layer of fibers.
    z_offset = index * ply_thickness
    layer_rotation = index * rotation_angle

    # Create an empty object to group fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_offset))
    layer_empty = bpy.context.object

    fiber_diameter = ply_thickness
    fiber_count = max(1, int(plate_size / fiber_diameter))

    total_fiber_space = fiber_count * fiber_diameter
    remaining_space = plate_size - total_fiber_space
    starting_y = -plate_size / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_center_y = starting_y + i * fiber_diameter
        fiber_instance = place_fiber(
            fiber_type=fiber_type,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_center_y,
            z_pos=z_offset
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_center_y, 0)

    # Select and activate the layer_empty before applying rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(layer_rotation),
        orient_axis='Z'
    )

    return layer_empty

# Generate the structure
for i in range(ply_count):
    form_layer(i)
