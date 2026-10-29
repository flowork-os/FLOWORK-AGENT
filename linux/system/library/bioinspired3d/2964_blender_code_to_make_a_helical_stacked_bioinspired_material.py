# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_to_make_a_helical_stacked_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code to make a helical stacked bioinspired material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
layers_count = 10  # Total number of layers
angle_per_layer = 15  # Degrees of rotation for each layer

def generate_layer(layer_index):
    # Function to create a single layer of the helical structure.
    height_of_structure = 2  # Overall height of the structure
    cube_size = 2  # Dimension of each layer's cube
    layer_thickness = height_of_structure / layers_count  # Thickness of each layer

    # Calculate the vertical position for the layer
    vertical_position = layer_index * layer_thickness

    # Add a cube at the specified location
    bpy.ops.mesh.primitive_cube_add(
        size=cube_size,
        location=(0, 0, vertical_position)
    )

    layer = bpy.context.object
    layer.scale[2] = layer_thickness / 2  # Scale the layer to make it thin

    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)  # Ensure the layer is selected

    # Rotate the layer around the Z-axis
    bpy.ops.transform.rotate(
        value=math.radians(layer_index * angle_per_layer),
        orient_axis='Z'
    )

    return layer

# Create the helical structure by looping through the layers
for index in range(layers_count):
    generate_layer(index)
