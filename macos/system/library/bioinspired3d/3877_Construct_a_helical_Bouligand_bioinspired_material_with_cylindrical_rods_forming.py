# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_helical_Bouligand_bioinspired_material_with_cylindrical_rods_forming" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a helical Bouligand bioinspired material with cylindrical rods forming each layer in Blender Python script think step by step.

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical fiber structure
layer_count = 14  # Number of layers
angle_increment = 20  # Degrees of rotation for each layer
fiber_shape = 'cylinder'  # Type of fiber shape

# Dimensions of the structure
full_height = 2.0  # Total height of the structure
plate_side = 2.0  # Width and depth of the plates
layer_thickness = full_height / layer_count  # Thickness of each layer

def create_fiber(shape, diameter, location):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_side,
            location=location,
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def construct_layer(layer_index):
    z_position = layer_index * layer_thickness
    rotation_angle = layer_index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_layer = bpy.context.object

    fiber_radius = layer_thickness
    fiber_count = max(1, int(plate_side / fiber_radius))

    total_fiber_length = fiber_count * fiber_radius
    extra_space = plate_side - total_fiber_length
    start_y = -plate_side / 2 + (fiber_radius / 2) + (extra_space / 2)

    for i in range(fiber_count):
        fiber_y = start_y + i * fiber_radius
        fiber_instance = create_fiber(
            shape=fiber_shape,
            diameter=fiber_radius,
            location=(0, fiber_y, z_position)
        )
        fiber_instance.parent = empty_layer
        fiber_instance.location = (0, fiber_y, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_layer
    empty_layer.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return empty_layer

# Generate the helical structure
for i in range(layer_count):
    construct_layer(i)
