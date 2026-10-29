# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_a_helical_twisted_ply_bioinspired_structure_with_cylindrical_rod" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of a helical twisted ply bioinspired structure with cylindrical rods forming each layer using python blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for helical fiber model
layers = 12  # Number of layers in the helical model
angle_increment = 15  # Degrees of rotation per layer
fiber_kind = 'cylinder'  # Type of fiber

# Dimensions of the complete structure
overall_height = 2  # Total height of the structure
plate_dimension = 2  # Width and length of each square plate
layer_thickness = overall_height / layers  # Thickness of each layer


def create_fiber_instance(shape, diameter, x_pos, y_pos, z_pos):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object


def construct_layer(layer_index):
    # Constructs a helical layer of fibers.
    z_position = layer_index * layer_thickness
    rotation_value = layer_index * angle_increment

    # Create a parent empty object
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_radius = layer_thickness
    fiber_count = max(1, int(plate_dimension / fiber_radius))

    total_fiber_space = fiber_count * fiber_radius
    remaining_space = plate_dimension - total_fiber_space
    initial_y_position = -plate_dimension / 2 + (fiber_radius / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_position = initial_y_position + i * fiber_radius
        fiber_instance = create_fiber_instance(
            shape=fiber_kind,
            diameter=fiber_radius,
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
        value=math.radians(rotation_value),
        orient_axis='Z'
    )

    return layer_empty

# Generate the entire structure
for i in range(layers):
    construct_layer(i)
