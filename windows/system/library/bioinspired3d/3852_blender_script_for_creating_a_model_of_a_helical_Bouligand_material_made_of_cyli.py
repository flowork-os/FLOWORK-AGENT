# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_creating_a_model_of_a_helical_Bouligand_material_made_of_cyli" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for creating a model of a helical Bouligand material made of cylindrical fibers. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 8  # Number of layers in the structure
rotation_step = 20  # Degrees of rotation for each layer
fiber_style = 'cylinder'  # Fiber shape

total_height = 2.0  # Height of the complete structure
square_plate_size = 2.0  # Width and length of each square plate
layer_thickness = total_height / layer_count  # Thickness of each layer

def place_fiber(shape, diameter, x_coord, y_coord, z_coord):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=square_plate_size,
            location=(x_coord, y_coord, z_coord),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def create_layer(layer_number):
    z_coord = layer_number * layer_thickness
    current_angle = layer_number * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_coord))
    layer_empty = bpy.context.object

    fiber_radius = layer_thickness
    num_of_fibers = max(1, int(square_plate_size / fiber_radius))

    total_fiber_length = num_of_fibers * fiber_radius
    space_remaining = square_plate_size - total_fiber_length
    initial_y_coord = -square_plate_size / 2 + (fiber_radius / 2) + (space_remaining / 2)

    for i in range(num_of_fibers):
        fiber_y_coord = initial_y_coord + i * fiber_radius
        fiber_instance = place_fiber(
            shape=fiber_style,
            diameter=fiber_radius,
            x_coord=0,
            y_coord=fiber_y_coord,
            z_coord=z_coord
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_y_coord, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(current_angle),
        orient_axis='Z'
    )

    return layer_empty

for layer in range(layer_count):
    create_layer(layer)
