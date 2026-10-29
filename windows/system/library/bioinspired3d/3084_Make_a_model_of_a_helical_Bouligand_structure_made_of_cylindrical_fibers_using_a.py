# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_a_helical_Bouligand_structure_made_of_cylindrical_fibers_using_a" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of a helical Bouligand structure made of cylindrical fibers using a Blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for helical fiber structure
layers_count = 10  # Total number of layers
angle_per_layer = 15  # Degrees of rotation for each layer
fiber_type = 'cylinder'  # Type of fiber used

# Dimensions of the structure
structure_height = 2.0  # Overall height of the entire structure
plate_dimension = 2.0  # Length and width of each square plate
layer_thickness = structure_height / layers_count  # Thickness of each layer

def create_fiber(fiber_type, diameter, x_pos, y_pos, z_pos, thickness):
    if fiber_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object


def build_layer(layer_index):
    # Constructs a helical structure using layers of fibers.
    height_offset = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    # Create a parent object for fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_offset))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    space_for_fibers = fiber_count * fiber_diameter
    remaining_space = plate_dimension - space_for_fibers
    initial_y = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        current_y = initial_y + i * fiber_diameter
        fiber_instance = create_fiber(
            fiber_type=fiber_type,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=current_y,
            z_pos=height_offset,
            thickness=layer_thickness
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, current_y, 0)

    # Select and activate the layer_empty before applying rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_empty

# Build the structure
for index in range(layers_count):
    build_layer(index)
