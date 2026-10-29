# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_code__construct_a_helical_bioinspired_structure_Think_step_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender code, construct a helical bioinspired structure Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical model
layers_count = 10  # Total number of layers in the helical structure
angle_per_layer = 15  # Angle of rotation for each layer in degrees

# Function to create an individual layer
def generate_layer(layer_index):
    height_of_structure = 2  # Overall height of the helical formation
    plate_dimension = 2  # Size of each square plate
    layer_thickness = height_of_structure / layers_count  # Thickness of each layer

    # Determine the vertical position of the current layer
    vertical_position = layer_index * layer_thickness

    # Add a cube at the specified location
    bpy.ops.mesh.primitive_cube_add(size=plate_dimension, location=(0, 0, vertical_position))

    # Reference to the newly created object
    layer_plate = bpy.context.object

    # Adjust the scale in the Z direction to form a thin layer
    layer_plate.scale[2] = layer_thickness / 2

    # Set the current plate as active and selected
    bpy.context.view_layer.objects.active = layer_plate
    layer_plate.select_set(True)

    # Rotate around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(layer_index * angle_per_layer), orient_axis='Z')

    return layer_plate

# Build the helical structure by looping through the specified number of layers
for index in range(layers_count):
    generate_layer(index)
