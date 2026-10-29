# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_a_helical_twisted_ply_structure_made_of_cylindrical_fibers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of a helical twisted ply structure made of cylindrical fibers in Blender code think step by step

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
layer_count = 7
angle_per_layer = 20
fiber_type = 'cylinder'

# Dimensions of the structure
full_height = 2
plate_dimension = 2
layer_thickness = full_height / layer_count

def add_cylinder(shape, diameter, position):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=position,
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

for layer_index in range(layer_count):
    z_position = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    # Create an empty object to hold the fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    fiber_parent = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_length = fiber_count * fiber_diameter
    remaining_space = plate_dimension - total_fiber_length
    starting_y = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_position = starting_y + i * fiber_diameter
        fiber_instance = add_cylinder(
            shape=fiber_type,
            diameter=fiber_diameter,
            position=(0, fiber_y_position, z_position)
        )
        fiber_instance.parent = fiber_parent
        fiber_instance.location = (0, fiber_y_position, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = fiber_parent
    fiber_parent.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
