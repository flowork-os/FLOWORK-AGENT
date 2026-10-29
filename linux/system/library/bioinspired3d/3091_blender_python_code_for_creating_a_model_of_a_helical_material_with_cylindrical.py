# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_creating_a_model_of_a_helical_material_with_cylindrical" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for creating a model of a helical material with cylindrical rods forming each layer.

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical fiber design
num_layers = 7  # Number of layers in the helical structure
angle_per_layer = 10  # Rotation angle for each layer
fiber_shape_type = 'cylinder'  # Shape of the fibers

# Dimensions of the structure
height_of_structure = 2  # Total height of the structure
size_of_plate = 2  # Dimensions of each plate
thickness_of_layer = height_of_structure / num_layers  # Thickness of each layer

# Function to create a fiber
def create_fiber_object(shape_type, diameter, x_coord, y_coord, z_coord):
    if shape_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=size_of_plate,
            location=(x_coord, y_coord, z_coord),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

# Function to create a layer
def generate_layer(layer_index):
    z_coordinate = layer_index * thickness_of_layer
    rotation_angle = layer_index * angle_per_layer

    # Create an empty to group fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_coordinate))
    layer_empty_object = bpy.context.object

    fiber_diameter = thickness_of_layer
    number_of_fibers = max(1, int(size_of_plate / fiber_diameter))

    total_fiber_space = number_of_fibers * fiber_diameter
    remaining_space = size_of_plate - total_fiber_space
    start_y_coordinate = -size_of_plate / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(number_of_fibers):
        fiber_y_coordinate = start_y_coordinate + i * fiber_diameter
        fiber_instance = create_fiber_object(
            shape_type=fiber_shape_type,
            diameter=fiber_diameter,
            x_coord=0,
            y_coord=fiber_y_coordinate,
            z_coord=z_coordinate
        )
        fiber_instance.parent = layer_empty_object
        fiber_instance.location = (0, fiber_y_coordinate, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty_object
    layer_empty_object.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_empty_object

# Build the structure
for i in range(num_layers):
    generate_layer(i)
