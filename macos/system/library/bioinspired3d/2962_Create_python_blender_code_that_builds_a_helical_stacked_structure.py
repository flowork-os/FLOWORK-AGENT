# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_python_blender_code_that_builds_a_helical_stacked_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create python blender code that builds a helical stacked structure.

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical model
num_layers = 12  # Total layers in the helical structure
angle_step = 5  # Degrees of rotation for each layer

def add_helical_layer(layer_num):
    # Add a layer to the helical structure
    total_height = 2
    layer_size = 2
    layer_height = total_height / num_layers

    # Calculate the layer's vertical position
    vertical_position = layer_num * layer_height

    # Create the cube layer
    bpy.ops.mesh.primitive_cube_add(
        size=layer_size,
        location=(0, 0, vertical_position)
    )

    current_layer = bpy.context.object
    current_layer.scale[2] = layer_height / 2

    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    # Rotate the layer around Z-axis
    bpy.ops.transform.rotate(
        value=math.radians(layer_num * angle_step),
        orient_axis='Z'
    )

# Construct the helical model by iterating through the layers
for i in range(num_layers):
    add_helical_layer(i)
