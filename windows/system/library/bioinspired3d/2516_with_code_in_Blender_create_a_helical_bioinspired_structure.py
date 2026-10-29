# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_code_in_Blender_create_a_helical_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with code in Blender create a helical bioinspired structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
layers_count = 10  # Total layers in the helical structure
angle_per_layer = 15  # Degrees of rotation for each layer

# Function to generate a single layer of the helix

def generate_layer(index):
    layer_height = 2  # Overall height of the structure
    layer_size = 2  # Size of each square layer
    thickness = layer_height / layers_count  # Thickness of each layer

    # Determine the vertical position for the layer
    z_position = index * thickness

    # Add a cube at the specified location
    bpy.ops.mesh.primitive_cube_add(size=layer_size, location=(0, 0, z_position))

    current_layer = bpy.context.object

    # Scale the cube to make it a thin layer
    current_layer.scale[2] = thickness / 2

    # Set the current layer as active
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    # Rotate the layer around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(index * angle_per_layer), orient_axis='Z')

    return current_layer

# Create the helical structure by looping through the number of layers
for i in range(layers_count):
    generate_layer(i)
