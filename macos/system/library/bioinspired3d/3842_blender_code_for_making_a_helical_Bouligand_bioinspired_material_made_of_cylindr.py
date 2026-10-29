# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_for_making_a_helical_Bouligand_bioinspired_material_made_of_cylindr" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code for making a helical Bouligand bioinspired material made of cylindrical fibers. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 8  # Number of layers in the structure
rotation_step = 20  # Rotation step for each layer
fiber_form = 'cylinder'  # Shape of fibers

complete_height = 2  # Total height of the structure
square_plate_size = 2  # Size of each plate
thickness_per_layer = complete_height / layer_count  # Thickness of each layer

def create_fiber_element(form, diameter, x_pos, y_pos, z_pos):
    if form == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=square_plate_size,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def construct_layer(index):
    z_position = index * thickness_per_layer
    rotation_value = index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty_object = bpy.context.object

    fiber_diameter = thickness_per_layer
    fiber_quantity = max(1, int(square_plate_size / fiber_diameter))

    total_fiber_space = fiber_quantity * fiber_diameter
    remaining_space = square_plate_size - total_fiber_space
    start_y_position = -square_plate_size / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_quantity):
        fiber_y_position = start_y_position + i * fiber_diameter
        fiber_instance = create_fiber_element(
            form=fiber_form,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_position,
            z_pos=z_position
        )
        fiber_instance.parent = layer_empty_object
        fiber_instance.location = (0, fiber_y_position, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty_object
    layer_empty_object.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_value),
        orient_axis='Z'
    )

    return layer_empty_object

for i in range(layer_count):
    construct_layer(i)
