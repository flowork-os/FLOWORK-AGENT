# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_script__generate_a_helical_Bouligand_bioinspired_material_with_eac" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender script, generate a helical Bouligand bioinspired material with each layer composed of aligned cylinders. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 9  # Total number of layers
angle_increment = 12  # Degree rotation for each layer
fiber_type = 'cylinder'  # Shape of the fibers

structure_height = 2  # Total height of the structure
plate_dimension = 2  # Width and length of each square plate
layer_thickness = structure_height / layer_count  # Thickness of each layer

def add_fiber_to_scene(fiber_shape, diameter, x_pos, y_pos, z_pos):
    if fiber_shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def create_layer(index):
    z_position = index * layer_thickness
    rotation_value = index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_space = fiber_count * fiber_diameter
    remaining_space = plate_dimension - total_fiber_space
    initial_y = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_position = initial_y + i * fiber_diameter
        fiber_instance = add_fiber_to_scene(
            fiber_shape=fiber_type,
            diameter=fiber_diameter,
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

for layer_index in range(layer_count):
    create_layer(layer_index)
