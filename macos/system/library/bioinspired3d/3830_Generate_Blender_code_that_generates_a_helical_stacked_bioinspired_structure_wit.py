# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_code_that_generates_a_helical_stacked_bioinspired_structure_wit" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender code that generates a helical stacked bioinspired structure with each layer composed of aligned cylinders Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

ply_count = 6  # Total number of plies
rotation_angle = 20  # Degrees of rotation for each successive ply
fiber_type = 'cylinder'  # Shape of fibers

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
    z_offset = index * ply_thickness
    layer_rotation = index * rotation_angle

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

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(layer_rotation),
        orient_axis='Z'
    )

    return layer_empty

for i in range(ply_count):
    form_layer(i)
