# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_a_helical_twisted_ply_structure_with_cylindrical_rods_formin" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of a helical twisted ply structure with cylindrical rods forming each layer in a Blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for helical fiber structure
number_of_layers = 9  # Total layers in the structure
angle_increment_per_layer = 20  # Degrees of rotation per layer
fiber_form = 'cylinder'  # Shape of fibers

# Overall dimensions
structure_height = 2  # Total height of the structure
size_of_plate = 2  # Size of each square plate
thickness_of_each_layer = structure_height / number_of_layers  # Thickness of each layer


def create_fiber_object(shape, diameter, x_pos, y_pos, z_pos):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=size_of_plate,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object


def build_helical_layer(layer_index):
    # Constructs a helical layer of fibers.
    z_coordinate = layer_index * thickness_of_each_layer
    rotation_value = layer_index * angle_increment_per_layer

    # Create an empty object for the layer
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_coordinate))
    empty_layer_object = bpy.context.object

    fiber_radius = thickness_of_each_layer
    number_of_fibers = max(1, int(size_of_plate / fiber_radius))

    total_fiber_space = number_of_fibers * fiber_radius
    space_left = size_of_plate - total_fiber_space
    initial_y_position = -size_of_plate / 2 + (fiber_radius / 2) + (space_left / 2)

    for i in range(number_of_fibers):
        fiber_y_position = initial_y_position + i * fiber_radius
        fiber_instance = create_fiber_object(
            shape=fiber_form,
            diameter=fiber_radius,
            x_pos=0,
            y_pos=fiber_y_position,
            z_pos=z_coordinate
        )
        fiber_instance.parent = empty_layer_object
        fiber_instance.location = (0, fiber_y_position, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_layer_object
    empty_layer_object.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_value),
        orient_axis='Z'
    )

    return empty_layer_object

# Generate the helical structure
for i in range(number_of_layers):
    build_helical_layer(i)
