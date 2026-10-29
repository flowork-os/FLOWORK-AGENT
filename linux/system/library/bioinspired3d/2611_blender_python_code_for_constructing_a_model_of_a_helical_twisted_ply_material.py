# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_constructing_a_model_of_a_helical_twisted_ply_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for constructing a model of a helical twisted ply material. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
layers_count = 10  # Total number of layers in the structure
angle_per_layer = 5  # Degrees of rotation for each layer

def build_layer(layer_index):
    height_of_structure = 2  # Overall height
    square_size = 2  # Size of each square plate
    thickness_of_layer = height_of_structure / layers_count  # Layer thickness

    # Calculate the vertical position of the layer
    vertical_position = layer_index * thickness_of_layer

    # Add a cube at the specified location
    bpy.ops.mesh.primitive_cube_add(size=square_size, location=(0, 0, vertical_position))
    layer_plate = bpy.context.object

    # Scale the cube to make it a thin plate
    layer_plate.scale[2] = thickness_of_layer / 2

    # Set the plate as the active object
    bpy.context.view_layer.objects.active = layer_plate
    layer_plate.select_set(True)

    # Rotate the plate around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(layer_index * angle_per_layer), orient_axis='Z')

    return layer_plate

# Create the helical structure
for index in range(layers_count):
    build_layer(index)
