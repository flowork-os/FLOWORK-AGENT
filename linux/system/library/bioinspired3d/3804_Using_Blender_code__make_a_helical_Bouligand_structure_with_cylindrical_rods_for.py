# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_Blender_code__make_a_helical_Bouligand_structure_with_cylindrical_rods_for" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using Blender code, make a helical Bouligand structure with cylindrical rods forming each layer. think step by step.

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
num_layers = 7  # Number of layers
angle_increment = 10  # Rotation angle for each layer
fiber_model = 'cylinder'  # Shape of fibers

# Overall dimensions
structure_height = 2  # Total height
square_size = 2  # Size of each square plate
layer_height = structure_height / num_layers  # Height of each layer

def generate_fiber(model, diameter, x_coord, y_coord, z_coord):
    if model == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=square_size,
            location=(x_coord, y_coord, z_coord),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def construct_layer(index):
    z_position = index * layer_height
    rotation_angle = index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_height
    fiber_count = max(1, int(square_size / fiber_diameter))

    total_fiber_space = fiber_count * fiber_diameter
    unused_space = square_size - total_fiber_space
    start_y = -square_size / 2 + (fiber_diameter / 2) + (unused_space / 2)

    for i in range(fiber_count):
        fiber_y_position = start_y + i * fiber_diameter
        fiber_instance = generate_fiber(
            model=fiber_model,
            diameter=fiber_diameter,
            x_coord=0,
            y_coord=fiber_y_position,
            z_coord=z_position
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
    return layer_empty

# Generate the helical structure
for layer_index in range(num_layers):
    construct_layer(layer_index)
