# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_script__build_a_helical_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender script, build a helical bioinspired material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
total_layers = 8  # Total number of layers
angle_per_layer = 10  # Rotation angle for each layer

def generate_layer(layer_index):
    # Function to create a single layer of the helical structure.
    height_of_structure = 2
    size_of_plate = 2
    thickness_of_layer = height_of_structure / total_layers

    # Calculate the vertical position for the current layer
    z_position = layer_index * thickness_of_layer

    # Add a cube at the specified location
    bpy.ops.mesh.primitive_cube_add(size=size_of_plate, location=(0, 0, z_position))
    layer = bpy.context.object

    # Scale the layer to make it thin
    layer.scale[2] = thickness_of_layer / 2

    # Set the layer as the active object
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    # Rotate the layer around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(layer_index * angle_per_layer), orient_axis='Z')

    return layer

# Create the helical structure
for index in range(total_layers):
    generate_layer(index)
