# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_a_helical_material_made_of_cylindrical_fibers_using_a_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of a helical material made of cylindrical fibers using a Blender code

import bpy
import math

# Clear existing objects in the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber arrangement
layer_count = 12  # Number of layers in the structure
rotation_step = 5  # Degrees of rotation for each layer
fiber_shape_type = 'cylinder'  # The shape of fibers

# Structure dimensions
height_of_structure = 2.0  # Overall height
plate_dimension = 2.0  # Length and width of each square plate
thickness_of_layer = height_of_structure / layer_count  # Thickness of each layer

# Function to create a fiber
def create_fiber_object(shape, diameter, x_pos, y_pos, z_pos):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

# Function to create a layer of fibers
def create_fiber_layer(layer_idx):
    # Builds a helical layer of fibers.
    z_position = layer_idx * thickness_of_layer
    rotation_angle = layer_idx * rotation_step

    # Create a new empty object for the layer
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = thickness_of_layer
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_space = fiber_count * fiber_diameter
    remaining_space = plate_dimension - total_fiber_space
    start_y = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y_pos = start_y + i * fiber_diameter
        fiber_instance = create_fiber_object(
            shape=fiber_shape_type,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_pos,
            z_pos=z_position
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_y_pos, 0)

    # Select the empty object before applying rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_empty

# Generate the helical structure
for idx in range(layer_count):
    create_fiber_layer(idx)
