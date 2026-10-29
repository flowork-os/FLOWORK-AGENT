# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_helical_stacked_structure_in_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a helical stacked structure in blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical model
layers_count = 10  # Total layers in the structure
angle_increment = 15  # Degrees of rotation per layer

def generate_layer(layer_index):
    height_of_structure = 2  # Complete height of the structure
    square_size = 2  # Size of the square plate
    layer_thickness = height_of_structure / layers_count  # Thickness of each layer

    # Calculate the vertical position for the current layer
    z_position = layer_index * layer_thickness

    # Create a cube at the specified position
    bpy.ops.mesh.primitive_cube_add(
        size=square_size,
        location=(0, 0, z_position)
    )

    current_layer = bpy.context.object

    # Scale the cube to form a thin plate
    current_layer.scale[2] = layer_thickness / 2

    # Set the current layer as active
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    # Rotate the layer around the Z-axis
    bpy.ops.transform.rotate(
        value=math.radians(layer_index * angle_increment),
        orient_axis='Z'
    )

    return current_layer

# Create the helical structure by looping through the number of layers
for index in range(layers_count):
    generate_layer(index)
