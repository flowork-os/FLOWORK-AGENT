# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_helical_Bouligand_structure_with_cylindrical_rods_forming_each_layer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a helical Bouligand structure with cylindrical rods forming each layer in python blender code

import bpy
import math

# Clear the current scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
num_layers = 12  # Total layers
rotation_angle = 5  # Degrees of rotation per layer
fiber_model = 'cylinder'  # Shape of the fibers

# Dimensions of the structure
height_of_structure = 2.0  # Total height
plate_dimension = 2.0  # Size of the plates
thickness_per_layer = height_of_structure / num_layers  # Layer thickness

def create_fiber_model(fiber_model, diameter, x_pos, y_pos, z_pos):
    if fiber_model == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def generate_layer(layer_index):
    z_position = layer_index * thickness_per_layer
    rotation_for_layer = layer_index * rotation_angle

    # Create an empty object to hold the fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_radius = thickness_per_layer
    fiber_count = max(1, int(plate_dimension / fiber_radius))

    total_fiber_width = fiber_count * fiber_radius
    space_remaining = plate_dimension - total_fiber_width
    starting_y = -plate_dimension / 2 + (fiber_radius / 2) + (space_remaining / 2)

    for i in range(fiber_count):
        fiber_center_y = starting_y + i * fiber_radius
        fiber_instance = create_fiber_model(
            fiber_model=fiber_model,
            diameter=fiber_radius,
            x_pos=0,
            y_pos=fiber_center_y,
            z_pos=z_position
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_center_y, 0)

    # Deselect all objects and select the empty object
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_for_layer),
        orient_axis='Z'
    )

    return layer_empty

# Create the helical structure
for index in range(num_layers):
    generate_layer(index)
