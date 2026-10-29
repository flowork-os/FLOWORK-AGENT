# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_Blender_Python_script__construct_a_helical_stacked_bioinspired_structure_wi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With Blender Python script, construct a helical stacked bioinspired structure with each layer composed of aligned cylinders. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 9  # Number of layers in the structure
rotation_angle = 12  # Rotation angle for each layer
fiber_shape = 'cylinder'  # Shape of fibers

height_of_structure = 2.0  # Total height of the structure
plate_dimensions = 2.0  # Dimensions of each square plate
layer_thickness = height_of_structure / layer_count  # Thickness for each layer

def add_fiber_shape(shape, diameter, x_pos, y_pos, z_pos):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimensions,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def generate_layer(index):
    z_position = index * layer_thickness
    rotation_for_layer = index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_count = max(1, int(plate_dimensions / fiber_diameter))

    total_fiber_space = fiber_count * fiber_diameter
    leftover_space = plate_dimensions - total_fiber_space
    starting_y_position = -plate_dimensions / 2 + (fiber_diameter / 2) + (leftover_space / 2)

    for i in range(fiber_count):
        fiber_y_position = starting_y_position + i * fiber_diameter
        fiber_instance = add_fiber_shape(
            shape=fiber_shape,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_position,
            z_pos=z_position
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_y_position, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_for_layer),
        orient_axis='Z'
    )

    return layer_empty

for i in range(layer_count):
    generate_layer(i)
