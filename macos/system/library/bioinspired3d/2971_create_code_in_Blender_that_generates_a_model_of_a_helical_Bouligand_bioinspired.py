# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_code_in_Blender_that_generates_a_model_of_a_helical_Bouligand_bioinspired" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create code in Blender that generates a model of a helical Bouligand bioinspired structure

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical parameters
num_layers = 12  # Number of layers in the helix
angle_step = 5  # Rotation angle for each layer

def add_layer(layer_index):
    height_total = 2  # Total height of the structure
    square_size = 2  # Size of the square layer
    layer_thickness = height_total / num_layers  # Thickness of each layer

    # Calculate the vertical position
    vertical_position = layer_index * layer_thickness

    # Create a cube at the calculated position
    bpy.ops.mesh.primitive_cube_add(size=square_size, location=(0, 0, vertical_position))
    current_layer = bpy.context.object

    # Scale the cube in the Z-direction
    current_layer.scale[2] = layer_thickness / 2

    # Set the current layer as active
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    # Rotate around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(layer_index * angle_step), orient_axis='Z')

# Generate the helical structure
for index in range(num_layers):
    add_layer(index)
