# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_blender_code_build_a_model_of_a_helical_stacked_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a blender code build a model of a helical stacked material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical assembly
layers_count = 10  # Total layers in the structure
angle_per_layer = 15  # Degrees of rotation for each layer

def generate_layer(layer_index):
    # Function to create a single layer of the helical structure.
    # Steps:
    # 1. Position the layer at the correct height.
    # 2. Scale it to form a thin layer.
    # 3. Rotate it around the Z-axis.
    
    total_height = 2  # Overall height of the structure
    square_size = 2  # Length of each square layer
    layer_thickness = total_height / layers_count  # Thickness of each layer

    # Calculate the vertical position for the layer
    height_position = layer_index * layer_thickness

    # Create a cube at the specified position
    bpy.ops.mesh.primitive_cube_add(
        size=square_size,
        location=(0, 0, height_position)
    )

    # Reference to the newly created object
    layer = bpy.context.object

    # Scale the cube to a thin layer
    layer.scale[2] = layer_thickness / 2

    # Set the layer as active and selected
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    # Rotate the layer around the Z-axis
    bpy.ops.transform.rotate(
        value=math.radians(layer_index * angle_per_layer),
        orient_axis='Z'
    )

    return layer

# Create the helical assembly by generating each layer
for index in range(layers_count):
    generate_layer(index)
