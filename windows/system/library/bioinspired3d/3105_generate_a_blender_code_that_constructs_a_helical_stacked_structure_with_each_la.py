# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_blender_code_that_constructs_a_helical_stacked_structure_with_each_la" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a blender code that constructs a helical stacked structure with each layer composed of aligned cylinders.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical structure
layers_count = 10  # Number of layers in the structure
angle_per_layer = 15  # Rotation angle for each layer
fiber_type = 'cylinder'  # Shape of the fibers

# Dimensions of the overall structure
structure_height = 2.0  # Total height of the structure
plate_dimension = 2.0  # Width and length of each square plate
layer_thickness = structure_height / layers_count  # Thickness of each layer

def create_fiber(fiber_type, diameter, x, y, z):
    if fiber_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def build_layer(layer_index):
    # Constructs a helical layer of fibers.
    height_offset = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    # Create an empty object to group fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_offset))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    num_fibers = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_space = num_fibers * fiber_diameter
    remaining_space = plate_dimension - total_fiber_space
    starting_y = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(num_fibers):
        fiber_y_position = starting_y + i * fiber_diameter
        fiber = create_fiber(
            fiber_type=fiber_type,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y_position,
            z=height_offset
        )
        fiber.parent = layer_empty
        fiber.location = (0, fiber_y_position, 0)

    # Select and activate the layer_empty before applying rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_empty

# Generate the helical structure
for i in range(layers_count):
    build_layer(i)
