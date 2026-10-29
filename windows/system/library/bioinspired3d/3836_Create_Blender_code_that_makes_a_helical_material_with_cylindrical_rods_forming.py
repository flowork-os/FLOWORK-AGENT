# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_Blender_code_that_makes_a_helical_material_with_cylindrical_rods_forming" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create Blender code that makes a helical material with cylindrical rods forming each layer think step by step.

import bpy
import math

# Remove existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
num_layers = 6
angle_increment = 10
fiber_form = 'cylinder'

# Structure dimensions
total_height = 2
base_plate_size = 2
layer_height = total_height / num_layers

def create_cylinder(shape, diameter, position):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=base_plate_size,
            location=position,
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

for layer_index in range(num_layers):
    z_level = layer_index * layer_height
    angle = layer_index * angle_increment

    # Create a parent empty object for fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_level))
    empty_object = bpy.context.object

    fiber_diameter = layer_height
    fiber_count = max(1, int(base_plate_size / fiber_diameter))

    total_fiber_length = fiber_count * fiber_diameter
    remaining_space = base_plate_size - total_fiber_length
    initial_y = -base_plate_size / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_position = initial_y + i * fiber_diameter
        fiber_instance = create_cylinder(
            shape=fiber_form,
            diameter=fiber_diameter,
            position=(0, fiber_y_position, z_level)
        )
        fiber_instance.parent = empty_object
        fiber_instance.location = (0, fiber_y_position, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_object
    empty_object.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(angle), orient_axis='Z')
