# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_a_helical_Bouligand_material_where_each_ply_consists_of_cyli" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of a helical Bouligand material where each ply consists of cylindrical fibers using blender code Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
layers = 12  # Number of layers
angle_increment = 5  # Degrees of rotation for each layer
fiber_style = 'cylinder'  # Fiber shape type

# Structure dimensions
total_height = 2  # Overall height
plate_dim = 2  # Dimensions of each plate
layer_height = total_height / layers  # Height of each layer

# Function to add a fiber
def add_fiber_shape(style, diameter, x_coord, y_coord, z_coord):
    if style == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dim,
            location=(x_coord, y_coord, z_coord),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

# Function to create a single layer
def build_layer(layer_num):
    z_pos = layer_num * layer_height
    rotation_amount = layer_num * angle_increment

    # Create an empty object to hold fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_pos))
    empty_layer = bpy.context.object

    fiber_diameter = layer_height
    fiber_count = max(1, int(plate_dim / fiber_diameter))

    total_fiber_area = fiber_count * fiber_diameter
    remaining_area = plate_dim - total_fiber_area
    start_y_position = -plate_dim / 2 + (fiber_diameter / 2) + (remaining_area / 2)

    for i in range(fiber_count):
        fiber_y_pos = start_y_position + i * fiber_diameter
        fiber = add_fiber_shape(
            style=fiber_style,
            diameter=fiber_diameter,
            x_coord=0,
            y_coord=fiber_y_pos,
            z_coord=z_pos
        )
        fiber.parent = empty_layer
        fiber.location = (0, fiber_y_pos, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_layer
    empty_layer.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_amount),
        orient_axis='Z'
    )

    return empty_layer

# Create the helical structure
for idx in range(layers):
    build_layer(idx)
