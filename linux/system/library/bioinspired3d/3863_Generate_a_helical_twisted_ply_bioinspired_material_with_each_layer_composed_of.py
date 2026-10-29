# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_helical_twisted_ply_bioinspired_material_with_each_layer_composed_of" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a helical twisted ply bioinspired material with each layer composed of aligned cylinders using Blender Python script Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layers_count = 7  # Total number of layers
rotation_step = 18  # Degree rotation for each layer
fiber_shape = 'cylinder'  # Shape of the fibers

structure_height = 2.0  # Height of the structure
plate_size = 2.0  # Size of each plate
layer_thickness = structure_height / layers_count  # Thickness of each layer

def create_fiber_shape(fiber_shape, diameter, x, y, z):
    if fiber_shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_size,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def build_helical_layer(layer_index):
    z_position = layer_index * layer_thickness
    rotation_angle = layer_index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_radius = layer_thickness
    fiber_count = max(1, int(plate_size / fiber_radius))

    total_fiber_width = fiber_count * fiber_radius
    free_space = plate_size - total_fiber_width
    starting_y = -plate_size / 2 + (fiber_radius / 2) + (free_space / 2)

    for i in range(fiber_count):
        fiber_center_y = starting_y + i * fiber_radius
        fiber_instance = create_fiber_shape(
            fiber_shape=fiber_shape,
            diameter=fiber_radius,
            x=0,
            y=fiber_center_y,
            z=z_position
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_center_y, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_empty

for index in range(layers_count):
    build_helical_layer(index)
