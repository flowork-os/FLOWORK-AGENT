# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_blender_code__build_a_helical_Bouligand_bioinspired_structure_where_e" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a blender code, build a helical Bouligand bioinspired structure where each ply consists of cylindrical fibers. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 7  # Number of layers in the helical structure
rotation_step = 12  # Rotation angle for each layer in degrees
fiber_form = 'cylinder'  # Fiber shape

full_height = 2
plate_dim = 2
layer_height = full_height / layer_count  # Calculate height of each layer

def create_fiber_object(shape, diameter, loc):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dim,
            location=loc,
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def construct_layer(index):
    z_loc = index * layer_height
    rotation_angle = index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_loc))
    empty_layer = bpy.context.object

    fiber_diameter = layer_height
    fiber_count = max(1, int(plate_dim / fiber_diameter))

    total_fiber_space = fiber_count * fiber_diameter
    remaining_space = plate_dim - total_fiber_space
    starting_y = -plate_dim / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_pos = starting_y + i * fiber_diameter
        fiber_instance = create_fiber_object(
            shape=fiber_form,
            diameter=fiber_diameter,
            loc=(0, fiber_y_pos, z_loc)
        )
        fiber_instance.parent = empty_layer
        fiber_instance.location = (0, fiber_y_pos, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_layer
    empty_layer.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return empty_layer

for i in range(layer_count):
    construct_layer(i)
