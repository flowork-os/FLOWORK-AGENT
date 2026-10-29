# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_constructing_a_helical_stacked_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for constructing a helical stacked bioinspired structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
num_layers = 7  # Number of layers in the helical model
rotation_angle = 10  # Rotation angle for each layer

def create_helical_layer(i):
    total_height = 2  # Total height of the helical structure
    plate_length = 2  # Length of each square plate
    thickness_per_layer = total_height / num_layers  # Calculate thickness

    # Calculate the Z position for the current layer
    z_position = i * thickness_per_layer

    # Create a cube at the calculated position
    bpy.ops.mesh.primitive_cube_add(size=plate_length, location=(0, 0, z_position))
    layer_object = bpy.context.object

    # Scale the cube to make it a thin plate
    layer_object.scale[2] = thickness_per_layer / 2

    # Set the object as active and selected
    bpy.context.view_layer.objects.active = layer_object
    layer_object.select_set(True)

    # Rotate the layer around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(i * rotation_angle), orient_axis='Z')

    return layer_object

# Loop to create the helical structure
for i in range(num_layers):
    create_helical_layer(i)
