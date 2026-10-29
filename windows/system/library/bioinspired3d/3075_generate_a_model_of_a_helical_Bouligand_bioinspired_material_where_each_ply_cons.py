# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_a_helical_Bouligand_bioinspired_material_where_each_ply_cons" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of a helical Bouligand bioinspired material where each ply consists of cylindrical fibers in Blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layers = 7  # Number of layers in the helical structure
rotation_step = 15  # Degrees of rotation for each layer
fiber_model = 'cylinder'  # Fiber model type

total_height = 2.0  # Height of the entire structure
plate_length = 2.0  # Length and width of each plate
thickness = total_height / layers  # Layer thickness


def add_cylinder(shape, diameter, position):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_length,
            location=position,
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object


def create_layer(layer_index):
    z_position = layer_index * thickness
    rotation_angle = layer_index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = thickness
    count_fibers = max(1, int(plate_length / fiber_diameter))

    total_fiber_space = count_fibers * fiber_diameter
    excess_space = plate_length - total_fiber_space
    initial_y = -plate_length / 2 + (fiber_diameter / 2) + (excess_space / 2)

    for i in range(count_fibers):
        fiber_y_position = initial_y + i * fiber_diameter
        fiber_object = add_cylinder(
            shape=fiber_model,
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

for i in range(layers):
    create_layer(i)
