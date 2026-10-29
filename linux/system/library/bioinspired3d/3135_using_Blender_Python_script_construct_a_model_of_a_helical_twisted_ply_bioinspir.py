# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_Python_script_construct_a_model_of_a_helical_twisted_ply_bioinspir" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender Python script construct a model of a helical twisted ply bioinspired material where each ply consists of cylindrical fibers.

import bpy
import math

# Clear the existing objects from the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical structure
layers = 6  # Total number of layers
angle_per_layer = 20  # Degrees of rotation for each layer
fiber_shape = 'cylinder'  # Shape of fibers

# Structure dimensions
height = 2
plate_size = 2
thickness = height / layers  # Thickness of each layer


def create_fiber(shape, diameter, location):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_size,
            location=location,
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object


def add_helical_layer(layer_index):
    # Function to add a layer of fibers in a helical manner.
    z_position = layer_index * thickness
    rotation_angle = layer_index * angle_per_layer

    # Create an empty object to hold the fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = thickness
    fiber_count = max(1, int(plate_size / fiber_diameter))

    total_fiber_length = fiber_count * fiber_diameter
    leftover_space = plate_size - total_fiber_length
    start_y = -plate_size / 2 + (fiber_diameter / 2) + (leftover_space / 2)

    for i in range(fiber_count):
        fiber_y = start_y + i * fiber_diameter
        fiber_instance = create_fiber(
            shape=fiber_shape,
            diameter=fiber_diameter,
            location=(0, fiber_y, z_position)
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_y, 0)

    # Deselect all and select the empty object before rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_empty

# Generate the helical structure
for i in range(layers):
    add_helical_layer(i)
