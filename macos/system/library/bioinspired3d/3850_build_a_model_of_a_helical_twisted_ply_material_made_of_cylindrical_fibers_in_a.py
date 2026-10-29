# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_a_helical_twisted_ply_material_made_of_cylindrical_fibers_in_a" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of a helical twisted ply material made of cylindrical fibers in a blender code Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure parameters
num_layers = 7  # Total layers in the structure
angle_per_layer = 10  # Rotation angle for each layer
fiber_form = 'cylinder'  # Type of fibers

# Structure dimensions
height_of_structure = 2.0  # Complete height of the structure
size_of_plate = 2.0  # Dimensions of each plate
thickness_of_layer = height_of_structure / num_layers  # Thickness calculated

def add_cylinder(fiber_form, diameter, x_loc, y_loc, z_loc):
    if fiber_form == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=size_of_plate,
            location=(x_loc, y_loc, z_loc),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def build_layer(layer_index):
    z_position = layer_index * thickness_of_layer
    layer_rotation = layer_index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_layer = bpy.context.object

    fiber_diameter = thickness_of_layer
    count_of_fibers = max(1, int(size_of_plate / fiber_diameter))

    total_length_of_fibers = count_of_fibers * fiber_diameter
    extra_space = size_of_plate - total_length_of_fibers
    starting_y = -size_of_plate / 2 + (fiber_diameter / 2) + (extra_space / 2)

    for i in range(count_of_fibers):
        fiber_y = starting_y + i * fiber_diameter
        new_fiber = add_cylinder(
            fiber_form=fiber_form,
            diameter=fiber_diameter,
            x_loc=0,
            y_loc=fiber_y,
            z_loc=z_position
        )
        new_fiber.parent = empty_layer
        new_fiber.location = (0, fiber_y, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_layer
    empty_layer.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(layer_rotation),
        orient_axis='Z'
    )

    return empty_layer

# Create the helical structure
for layer in range(num_layers):
    build_layer(layer)
