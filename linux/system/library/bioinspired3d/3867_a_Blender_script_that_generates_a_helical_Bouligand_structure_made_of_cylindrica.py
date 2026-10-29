# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_generates_a_helical_Bouligand_structure_made_of_cylindrica" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that generates a helical Bouligand structure made of cylindrical fibers think step by step

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure configuration
num_layers = 6  # Total layers
angle_increment = 20  # Rotation angle for each layer
fiber_shape = 'cylinder'  # Type of fiber

# Dimensions of the structure
structure_height = 2.0  # Height of the structure
plate_length = 2.0  # Length of each plate
thickness_per_layer = structure_height / num_layers  # Thickness of each layer

# Function to add a fiber
def create_fiber(shape, diameter, x, y, z):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_length,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

# Function to create a layer of fibers
def build_layer(layer_idx):
    z_position = layer_idx * thickness_per_layer
    rotation_angle = layer_idx * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = thickness_per_layer
    fiber_count = max(1, int(plate_length / fiber_diameter))

    total_fiber_space = fiber_count * fiber_diameter
    leftover_space = plate_length - total_fiber_space
    start_y = -plate_length / 2 + (fiber_diameter / 2) + (leftover_space / 2)

    for i in range(fiber_count):
        fiber_y = start_y + i * fiber_diameter
        fiber_instance = create_fiber(
            shape=fiber_shape,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y,
            z=z_position
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_y, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_empty

# Generate the helical structure
for idx in range(num_layers):
    build_layer(idx)
