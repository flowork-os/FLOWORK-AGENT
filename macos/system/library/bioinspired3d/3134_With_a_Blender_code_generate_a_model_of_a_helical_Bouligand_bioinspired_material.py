# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_code_generate_a_model_of_a_helical_Bouligand_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender code generate a model of a helical Bouligand bioinspired material made of cylindrical fibers.

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for creating the helical structure
num_layers = 12  # Number of layers in the structure
angle_increment = 10  # Rotation angle for each layer
fiber_type = 'cylinder'  # Fiber shape

# Dimensions of the structure
total_height = 2
plate_dim = 2
layer_height = total_height / num_layers  # Calculate the height of each layer


def create_fiber_object(shape, diameter, position):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dim,
            location=position,
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object


def generate_layer(layer_index):
    # Function to generate a layer of fibers in a helical arrangement.
    z_position = layer_index * layer_height
    rotation_value = layer_index * angle_increment

    # Create an empty object for the fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_layer = bpy.context.object

    fiber_diameter = layer_height
    fiber_count = max(1, int(plate_dim / fiber_diameter))

    total_fiber_space = fiber_count * fiber_diameter
    remaining_space = plate_dim - total_fiber_space
    start_y_position = -plate_dim / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_position = start_y_position + i * fiber_diameter
        fiber_instance = create_fiber_object(
            shape=fiber_type,
            diameter=fiber_diameter,
            position=(0, fiber_y_position, z_position)
        )
        fiber_instance.parent = empty_layer
        fiber_instance.location = (0, fiber_y_position, 0)

    # Deselect all and set the empty object as active
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_layer
    empty_layer.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_value),
        orient_axis='Z'
    )

    return empty_layer

# Create the entire helical structure
for i in range(num_layers):
    generate_layer(i)
