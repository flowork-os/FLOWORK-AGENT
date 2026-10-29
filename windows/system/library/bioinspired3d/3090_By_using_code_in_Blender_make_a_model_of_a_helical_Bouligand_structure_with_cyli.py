# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_code_in_Blender_make_a_model_of_a_helical_Bouligand_structure_with_cyli" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using code in Blender make a model of a helical Bouligand structure with cylindrical rods forming each layer

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Total number of layers
rotation_angle = 15  # Degrees of rotation for each layer
fiber_type = 'cylinder'  # Type of fiber shape

# Dimensions of the overall structure
structure_height = 2  # Complete height of the structure
plate_dimension = 2  # Width and length of each plate
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


def add_layer(layer_index):
    z_position = layer_index * layer_thickness
    rotation_offset = layer_index * rotation_angle

    # Create an empty object to hold fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_radius = layer_thickness
    total_fibers = max(1, int(plate_dimension / fiber_radius))

    spacing = plate_dimension - (total_fibers * fiber_radius)
    start_y_position = -plate_dimension / 2 + (fiber_radius / 2) + (spacing / 2)

    for i in range(total_fibers):
        fiber_y_position = start_y_position + i * fiber_radius
        fiber_instance = create_fiber(
            shape=fiber_type,
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
        value=math.radians(rotation_offset),
        orient_axis='Z'
    )

    return layer_empty

# Create the complete structure
for index in range(layers_count):
    add_layer(index)
