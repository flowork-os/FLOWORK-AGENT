# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_script_that_creates_a_model_of_a_helical_Bouligand_structure_ma" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender script that creates a model of a helical Bouligand structure made of cylindrical fibers. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_amount = 11  # Number of layers
angle_increment = 12  # Increment in degrees for each layer
fiber_type = 'cylinder'  # Type of fiber shape

full_height = 2  # Overall height of the structure
plate_dimension = 2  # Size of each plate
layer_depth = full_height / layer_amount  # Depth of each layer

def add_fiber(type_of_fiber, diameter, x_pos, y_pos, z_pos):
    if type_of_fiber == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def build_layer(index):
    z_position = index * layer_depth
    rotation_angle = index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_radius = layer_depth
    fiber_count = max(1, int(plate_dimension / fiber_radius))

    total_fiber_space = fiber_count * fiber_radius
    remaining_space = plate_dimension - total_fiber_space
    start_y_position = -plate_dimension / 2 + (fiber_radius / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_position = start_y_position + i * fiber_radius
        fiber_instance = add_fiber(
            type_of_fiber=fiber_type,
            diameter=fiber_radius,
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
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

for i in range(layer_amount):
    build_layer(i)
