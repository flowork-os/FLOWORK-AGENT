# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_for_building_a_model_of_a_helical_structure_Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code for building a model of a helical structure Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
layers_count = 10  # Total number of layers in the structure
angle_per_layer = 15  # Degrees of rotation for each layer

def generate_layer(layer_index):
    # Function to generate a single layer of the helical structure.
    height_of_structure = 2  # Overall height of the structure
    plate_dimension = 2  # Dimension of each square plate
    layer_thickness = height_of_structure / layers_count  # Thickness calculation for each layer

    # Determine vertical position for the layer
    vertical_position = layer_index * layer_thickness

    # Add a cube at the specified position
    bpy.ops.mesh.primitive_cube_add(
        size=plate_dimension,
        location=(0, 0, vertical_position)
    )

    # Reference the newly created object
    layer_plate = bpy.context.object

    # Scale the plate in the Z-axis to achieve the desired thickness
    layer_plate.scale[2] = layer_thickness / 2

    # Set the plate as active and selected
    bpy.context.view_layer.objects.active = layer_plate
    layer_plate.select_set(True)

    # Rotate the plate around the Z-axis
    bpy.ops.transform.rotate(
        value=math.radians(layer_index * angle_per_layer),
        orient_axis='Z'
    )

    return layer_plate

# Build the helical structure by creating each layer
for index in range(layers_count):
    generate_layer(index)
