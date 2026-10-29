# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_python_blender_code__make_a_model_of_a_helical_twisted_ply_material_with_c" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using python blender code, make a model of a helical twisted ply material with cylindrical rods forming each layer

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

total_layers = 12  # Total layers in the structure
angle_increment = 10  # Degrees of rotation for each layer
fiber_form = 'cylinder'  # Shape of fibers

structure_height = 2.0  # Total height of the structure
plate_dimension = 2.0  # Size of each plate
layer_thickness = structure_height / total_layers  # Thickness of each layer


def create_fiber_object(fiber_type, diameter, position):
    if fiber_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=position,
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object


def generate_layer(layer_index):
    z_coordinate = layer_index * layer_thickness
    rotation_angle = layer_index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_coordinate))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_length = fiber_count * fiber_diameter
    remaining_space = plate_dimension - total_fiber_length
    start_y = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_position = start_y + i * fiber_diameter
        fiber_object = create_fiber_object(
            fiber_type=fiber_form,
            diameter=fiber_diameter,
            position=(0, fiber_y_position, z_coordinate)
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

for index in range(total_layers):
    generate_layer(index)
