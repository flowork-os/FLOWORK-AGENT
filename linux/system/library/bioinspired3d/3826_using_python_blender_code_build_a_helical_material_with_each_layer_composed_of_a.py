# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_python_blender_code_build_a_helical_material_with_each_layer_composed_of_a" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using python blender code build a helical material with each layer composed of aligned cylinders. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layers = 8  # Total number of layers
rotation_angle = 20  # Degrees of rotation for each layer
fiber_shape_type = 'cylinder'  # Shape of the fibers

height_of_structure = 2  # Total height of the structure
size_of_plate = 2  # Width and length of each plate
thickness_of_layers = height_of_structure / layers  # Thickness of each layer

def add_cylinder(shape, diameter, x_location, y_location, z_location):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=size_of_plate,
            location=(x_location, y_location, z_location),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def create_layer(index):
    z_position = index * thickness_of_layers
    rotation_value = index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = thickness_of_layers
    number_of_fibers = max(1, int(size_of_plate / fiber_diameter))

    fiber_total_space = number_of_fibers * fiber_diameter
    space_left = size_of_plate - fiber_total_space
    start_y_position = -size_of_plate / 2 + (fiber_diameter / 2) + (space_left / 2)

    for i in range(number_of_fibers):
        fiber_y = start_y_position + i * fiber_diameter
        fiber_object = add_cylinder(
            shape=fiber_shape_type,
            diameter=fiber_diameter,
            x_location=0,
            y_location=fiber_y,
            z_location=z_position
        )
        fiber_object.parent = layer_empty
        fiber_object.location = (0, fiber_y, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_value),
        orient_axis='Z'
    )

    return layer_empty

for i in range(layers):
    create_layer(i)
