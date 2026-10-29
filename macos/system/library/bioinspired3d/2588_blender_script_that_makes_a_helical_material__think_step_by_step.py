# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_makes_a_helical_material__think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that makes a helical material. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical structure
layers_count = 10  # Total number of layers in the structure
angle_per_layer = 15  # Degrees of rotation for each layer

def generate_layer(layer_index):
    # Function to create a single layer in the helical structure.
    height_of_structure = 2  # Overall height of the structure
    layer_dimension = 2  # Dimensions of each square layer
    thickness_of_layer = height_of_structure / layers_count  # Calculate layer thickness

    # Determine the vertical position for the layer
    vertical_position = layer_index * thickness_of_layer

    # Add a cube mesh at the specified position
    bpy.ops.mesh.primitive_cube_add(size=layer_dimension, location=(0, 0, vertical_position))

    # Reference the newly created object
    current_layer = bpy.context.object

    # Scale the cube to create a thin layer
    current_layer.scale[2] = thickness_of_layer / 2

    # Set the layer as active and selected
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    # Rotate the layer around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(layer_index * angle_per_layer), orient_axis='Z')

    return current_layer

# Create the helical structure by looping through the layers
for index in range(layers_count):
    generate_layer(index)
