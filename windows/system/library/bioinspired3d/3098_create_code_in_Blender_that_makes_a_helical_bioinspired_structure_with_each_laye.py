# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_code_in_Blender_that_makes_a_helical_bioinspired_structure_with_each_laye" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create code in Blender that makes a helical bioinspired structure with each layer composed of aligned cylinders

import bpy
import math

# Clear the existing scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the parameters for the helical structure
layer_num = 8
rotation_step = 12
fiber_geom = 'cylinder'

# Dimensions of the entire structure
complete_height = 2
square_dimension = 2
layer_height = complete_height / layer_num

def create_fiber_object(shape, diameter, position):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=square_dimension,
            location=position,
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def generate_layer(layer_index):
    z_pos = layer_index * layer_height
    rotation_angle = layer_index * rotation_step

    # Create an empty parent object
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_pos))
    empty_layer = bpy.context.object

    fiber_diameter = layer_height
    fiber_count = max(1, int(square_dimension / fiber_diameter))

    total_fibers_space = fiber_count * fiber_diameter
    remaining_space = square_dimension - total_fibers_space
    start_y = -square_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y = start_y + i * fiber_diameter
        fiber = create_fiber_object(fiber_geom, fiber_diameter, (0, fiber_y, z_pos))
        fiber.parent = empty_layer
        fiber.location = (0, fiber_y, 0)

    # Rotate the empty object
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_layer
    empty_layer.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')

# Build the helical structure
for i in range(layer_num):
    generate_layer(i)
