# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_to_create_a_helical_Bouligand_structure_made_of_cylindrical" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code to create a helical Bouligand structure made of cylindrical fibers. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 12  # Number of layers in the structure
rotation_step = 5  # Degrees of rotation for each layer
fiber_shape_type = 'cylinder'  # The shape of fibers

height_of_structure = 2.0  # Overall height
plate_dimension = 2.0  # Length and width of each square plate
thickness_of_layer = height_of_structure / layer_count  # Thickness of each layer

def create_fiber_object(shape, diameter, x_pos, y_pos, z_pos):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def create_fiber_layer(layer_idx):
    z_position = layer_idx * thickness_of_layer
    rotation_angle = layer_idx * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = thickness_of_layer
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_space = fiber_count * fiber_diameter
    remaining_space = plate_dimension - total_fiber_space
    start_y = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_pos = start_y + i * fiber_diameter
        fiber_instance = create_fiber_object(
            shape=fiber_shape_type,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_pos,
            z_pos=z_position
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_y_pos, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_empty

for idx in range(layer_count):
    create_fiber_layer(idx)
