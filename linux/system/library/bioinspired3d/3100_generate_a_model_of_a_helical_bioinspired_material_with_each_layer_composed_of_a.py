# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_a_helical_bioinspired_material_with_each_layer_composed_of_a" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of a helical bioinspired material with each layer composed of aligned cylinders using a Blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Number of layers in the structure
rotation_angle = 15  # Degrees of rotation per layer
fiber_type = 'cylinder'  # Shape of fibers

# Dimensions of the overall structure
structure_height = 2.0  # Total height of the structure
plate_dimension = 2.0  # Width and length of each plate
layer_thickness = structure_height / layers_count  # Thickness of each layer

def create_fiber(fiber_type, diameter, x_pos, y_pos, z_pos):
    if fiber_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object


def construct_layer(layer_index):
    # Constructs a layer of fibers in a helical arrangement.
    z_position = layer_index * layer_thickness
    rotation_for_layer = layer_index * rotation_angle

    # Create a parent object for fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_length = fiber_count * fiber_diameter
    remaining_space = plate_dimension - total_fiber_length
    start_y_position = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for index in range(fiber_count):
        fiber_y_position = start_y_position + index * fiber_diameter
        fiber_object = create_fiber(
            fiber_type=fiber_type,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_position,
            z_pos=z_position
        )
        fiber_object.parent = layer_empty
        fiber_object.location = (0, fiber_y_position, 0)

    # Rotate the empty object to position the layer
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_for_layer),
        orient_axis='Z'
    )

    return layer_empty

# Create the helical structure
for index in range(layers_count):
    construct_layer(index)
