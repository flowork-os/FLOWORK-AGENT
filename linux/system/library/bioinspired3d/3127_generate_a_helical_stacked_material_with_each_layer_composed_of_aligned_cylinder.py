# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_helical_stacked_material_with_each_layer_composed_of_aligned_cylinder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a helical stacked material with each layer composed of aligned cylinders using code in Blender

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layer_count = 10  # Total number of layers
angle_increment = 15  # Degrees of rotation per layer
fiber_type = 'cylinder'  # Fiber geometry

# Dimensions of the structure
height_total = 2  # Overall height of the structure
plate_dimension = 2  # Dimensions of each plate
layer_thickness = height_total / layer_count  # Thickness of each layer

def create_fiber(fiber_type, diameter, x, y, z, thickness):
    if fiber_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object


def build_layer(index):
    # Build a layer of fibers in a helical arrangement.
    z_position = index * layer_thickness
    rotation_angle = index * angle_increment

    # Create an empty object to group fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_layer = bpy.context.object

    fiber_radius = layer_thickness
    fiber_count = max(1, int(plate_dimension / fiber_radius))

    total_fiber_length = fiber_count * fiber_radius
    remaining_space = plate_dimension - total_fiber_length
    initial_y = -plate_dimension / 2 + (fiber_radius / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_position = initial_y + i * fiber_radius
        fiber_instance = create_fiber(
            fiber_type=fiber_type,
            diameter=fiber_radius,
            x=0,
            y=fiber_y_position,
            z=z_position,
            thickness=layer_thickness
        )
        fiber_instance.parent = empty_layer
        fiber_instance.location = (0, fiber_y_position, 0)

    # Select and activate the empty layer for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_layer
    empty_layer.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return empty_layer

# Create the helical structure
for i in range(layer_count):
    build_layer(i)
