# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_code_that_creates_a_helical_bioinspired_structure_with_cylindric" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender code that creates a helical bioinspired structure with cylindrical rods forming each layer.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Total number of layers
angle_per_layer = 15  # Degrees of rotation for each layer
fiber_type = 'cylinder'  # Type of fiber shape

# Dimensions of the overall structure
complete_height = 2  # Height of the entire structure
plate_dimension = 2  # Size of each plate
layer_thickness = complete_height / layers_count  # Thickness of each layer

# Function to create a fiber
def create_fiber(type_of_fiber, diameter, x_pos, y_pos, z_pos):
    if type_of_fiber == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

# Function to create a single layer of fibers
def generate_layer(layer_index):
    z_position = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    # Create an empty object for the layer
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_radius = layer_thickness
    fiber_count = max(1, int(plate_dimension / fiber_radius))

    spacing = plate_dimension - (fiber_count * fiber_radius)
    start_y_position = -plate_dimension / 2 + (fiber_radius / 2) + (spacing / 2)

    for i in range(fiber_count):
        fiber_y_position = start_y_position + i * fiber_radius
        fiber_instance = create_fiber(
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

# Create the full structure
for layer in range(layers_count):
    generate_layer(layer)
