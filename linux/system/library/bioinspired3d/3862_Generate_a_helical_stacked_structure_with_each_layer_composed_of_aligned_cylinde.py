# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_helical_stacked_structure_with_each_layer_composed_of_aligned_cylinde" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a helical stacked structure with each layer composed of aligned cylinders in blender python code think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layers_total = 15  # Number of layers in the structure
angle_increment = 20  # Degrees to rotate for each layer
fiber_geom = 'cylinder'  # Fiber shape

final_structure_height = 2.0  # Height of the structure
plate_dimension = 2.0  # Size of each plate
layer_thickness = final_structure_height / layers_total  # Thickness of each layer

def place_fiber(fiber_geom, diameter, x_pos, y_pos, z_pos):
    if fiber_geom == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def construct_layer(layer_index):
    z_coord = layer_index * layer_thickness
    rotation_value = layer_index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_coord))
    layer_empty = bpy.context.object

    fiber_radius = layer_thickness
    fiber_count = max(1, int(plate_dimension / fiber_radius))

    total_fiber_length = fiber_count * fiber_radius
    remaining_space = plate_dimension - total_fiber_length
    initial_y = -plate_dimension / 2 + (fiber_radius / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_center_y = initial_y + i * fiber_radius
        fiber_instance = place_fiber(
            fiber_geom=fiber_geom,
            diameter=fiber_radius,
            x_pos=0,
            y_pos=fiber_center_y,
            z_pos=z_coord
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_center_y, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_value),
        orient_axis='Z'
    )

    return layer_empty

for index in range(layers_total):
    construct_layer(index)
