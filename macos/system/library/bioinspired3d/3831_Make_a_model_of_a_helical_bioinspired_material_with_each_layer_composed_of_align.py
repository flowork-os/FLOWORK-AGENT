# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_a_helical_bioinspired_material_with_each_layer_composed_of_align" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of a helical bioinspired material with each layer composed of aligned cylinders in a Blender code think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 8  # Number of layers
rotation_step = 5  # Rotation angle for each layer in degrees
fiber_style = 'cylinder'  # Type of fiber to be used

complete_height = 2.0  # Total height of the structure
plate_dim = 2.0  # Dimensions of each square plate
layer_height = complete_height / layer_count  # Height of each layer

def generate_fiber(style, diameter, x_coord, y_coord, z_coord):
    if style == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dim,
            location=(x_coord, y_coord, z_coord),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def construct_layer(index):
    z_position = index * layer_height
    rotation_angle = index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_group = bpy.context.object

    fiber_diameter = layer_height
    fiber_quantity = max(1, int(plate_dim / fiber_diameter))

    total_fiber_space = fiber_quantity * fiber_diameter
    remaining_space = plate_dim - total_fiber_space
    initial_y_coord = -plate_dim / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_quantity):
        current_y_coord = initial_y_coord + i * fiber_diameter
        fiber_instance = generate_fiber(
            style=fiber_style,
            diameter=fiber_diameter,
            x_coord=0,
            y_coord=current_y_coord,
            z_coord=z_position
        )
        fiber_instance.parent = layer_group
        fiber_instance.location = (0, current_y_coord, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_group
    layer_group.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_group

for i in range(layer_count):
    construct_layer(i)
