# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_a_blender_code__construct_a_model_of_a_helical_twisted_ply_structure_made" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using a blender code, construct a model of a helical twisted ply structure made of cylindrical fibers. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber assembly
number_of_layers = 9  # Total layers in the structure
rotation_increment = 12  # Degrees of rotation for each layer
fiber_geometry = 'cylinder'  # Type of fiber shape

# Dimensions of the structure
structure_height = 2.0  # Total height of the assembly
plate_dimension = 2.0  # Width and length of each plate
layer_thickness = structure_height / number_of_layers  # Thickness of each layer

def create_fiber_object(geometry, diameter, x_pos, y_pos, z_pos):
    if geometry == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def construct_layer(layer_index):
    z_position = layer_index * layer_thickness
    rotation_angle = layer_index * rotation_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_space = fiber_count * fiber_diameter
    remaining_space = plate_dimension - total_fiber_space
    initial_y = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_pos = initial_y + i * fiber_diameter
        fiber_instance = create_fiber_object(
            geometry=fiber_geometry,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_pos,
            z_pos=z_position
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_y_pos, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_empty

# Generate the complete structure
for i in range(number_of_layers):
    construct_layer(i)
