# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_code__build_a_model_of_a_helical_Bouligand_structure_with_eac" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender code, build a model of a helical Bouligand structure with each layer composed of aligned cylinders

import bpy
import math

# Clear existing objects from the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical fiber structure
layers_count = 10  # Total number of layers in the structure
angle_per_layer = 15  # Rotation angle in degrees for each layer
fiber_type = 'cylinder'  # Type of fiber used

# Dimensions of the overall structure
structure_height = 2.0  # Final height of the structure
plate_dimension = 2.0  # Width and length of each square plate
layer_thickness = structure_height / layers_count  # Thickness of each layer

def create_fiber(fiber_type, diameter, x_pos, y_pos, z_pos):
    if fiber_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def build_layer(layer_index):
    z_position = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    # Create a parent empty object for the layer
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_radius = layer_thickness
    fiber_count = max(1, int(plate_dimension / fiber_radius))

    total_fiber_width = fiber_count * fiber_radius
    remaining_space = plate_dimension - total_fiber_width
    initial_y = -plate_dimension / 2 + (fiber_radius / 2) + (remaining_space / 2)

    for index in range(fiber_count):
        fiber_center_y = initial_y + index * fiber_radius
        fiber_instance = create_fiber(
            fiber_type=fiber_type,
            diameter=fiber_radius,
            x_pos=0,
            y_pos=fiber_center_y,
            z_pos=z_position
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_center_y, 0)

    # Activate the empty object to apply rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_empty

# Construct the structure
for index in range(layers_count):
    build_layer(index)
