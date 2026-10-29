# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_a_helical_Bouligand_bioinspired_material_with_cylindrical_rods" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of a helical Bouligand bioinspired material with cylindrical rods forming each layer in a blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Total layers in the helical structure
angle_increment = 15  # Degrees of rotation for each layer
fiber_type = 'cylinder'  # Type of fiber shape

# Overall dimensions of the structure
structure_height = 2.0  # Height of the entire structure
plate_dimension = 2.0  # Width and length of each plate
layer_thickness = structure_height / layers_count  # Thickness of each layer

def create_fiber(shape, diameter, x_pos, y_pos, z_pos):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object


def generate_layer(layer_index):
    # Function to create a layer of fibers in the helical structure.
    z_position = layer_index * layer_thickness
    rotation_angle = layer_index * angle_increment

    # Create an empty object for the layer
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_radius = layer_thickness
    fiber_count = max(1, int(plate_dimension / fiber_radius))

    total_fiber_space = fiber_count * fiber_radius
    remaining_space = plate_dimension - total_fiber_space
    start_y_position = -plate_dimension / 2 + (fiber_radius / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        current_fiber_y = start_y_position + i * fiber_radius
        fiber_instance = create_fiber(
            shape=fiber_type,
            diameter=fiber_radius,
            x_pos=0,
            y_pos=current_fiber_y,
            z_pos=z_position
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, current_fiber_y, 0)

    # Set the layer_empty as active and apply rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_empty

# Create the entire helical structure
for i in range(layers_count):
    generate_layer(i)
