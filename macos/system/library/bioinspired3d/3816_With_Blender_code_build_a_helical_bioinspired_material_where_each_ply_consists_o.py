# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_Blender_code_build_a_helical_bioinspired_material_where_each_ply_consists_o" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With Blender code build a helical bioinspired material where each ply consists of cylindrical fibers think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_layers = 9  # Number of layers in the structure
rotation_increment = 20  # Rotation angle for each layer
fiber_geometry = 'cylinder'  # Geometry of fibers

complete_height = 2.0  # Total height of the structure
plate_side = 2.0  # Dimensions of each plate
layer_height = complete_height / num_layers  # Height of each layer

def instantiate_fiber(fiber_shape, diameter, position):
    if fiber_shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_side,
            location=position,
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def construct_layer(layer_index):
    z_position = layer_index * layer_height
    rotation_angle = layer_index * rotation_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_height
    fiber_count = max(1, int(plate_side / fiber_diameter))

    total_fiber_space = fiber_count * fiber_diameter
    leftover_space = plate_side - total_fiber_space
    initial_y = -plate_side / 2 + (fiber_diameter / 2) + (leftover_space / 2)

    for i in range(fiber_count):
        fiber_y_position = initial_y + i * fiber_diameter
        fiber_object = instantiate_fiber(
            fiber_shape=fiber_geometry,
            diameter=fiber_diameter,
            position=(0, fiber_y_position, z_position)
        )
        fiber_object.parent = layer_empty
        fiber_object.location = (0, fiber_y_position, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_empty

for i in range(num_layers):
    construct_layer(i)
