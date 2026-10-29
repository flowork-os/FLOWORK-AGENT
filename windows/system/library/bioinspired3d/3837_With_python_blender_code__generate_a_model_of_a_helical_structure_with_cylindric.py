# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_python_blender_code__generate_a_model_of_a_helical_structure_with_cylindric" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With python blender code, generate a model of a helical structure with cylindrical rods forming each layer. think step by step.

import bpy
import math

# Clear the Blender scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers = 12
rotation_angle = 15
fiber_form = 'cylinder'

# Dimensions of the structure
height = 2
plate_dimension = 2
thickness = height / layers

def create_fiber_object(shape, diameter, position):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=position,
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

for i in range(layers):
    z_position = i * thickness
    current_rotation = i * rotation_angle

    # Create an empty object to group fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_fiber_group = bpy.context.object

    fiber_diameter = thickness
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_space = fiber_count * fiber_diameter
    leftover_space = plate_dimension - total_fiber_space
    start_y = -plate_dimension / 2 + (fiber_diameter / 2) + (leftover_space / 2)

    for j in range(fiber_count):
        fiber_y_position = start_y + j * fiber_diameter
        fiber_object = create_fiber_object(
            shape=fiber_form,
            diameter=fiber_diameter,
            position=(0, fiber_y_position, z_position)
        )
        fiber_object.parent = empty_fiber_group
        fiber_object.location = (0, fiber_y_position, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_fiber_group
    empty_fiber_group.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(current_rotation), orient_axis='Z')
