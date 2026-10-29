# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_Blender_code_that_builds_a_helical_stacked_structure_think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create Blender code that builds a helical stacked structure think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
layers_count = 10  # Total number of layers in the structure
angle_per_layer = 15  # Rotation angle in degrees for each layer

# Function to generate a single layer of the helical structure
def generate_layer(layer_index):
    height_of_structure = 2  # Overall height of the structure
    plate_dimension = 2  # Length of each square plate
    layer_thickness = height_of_structure / layers_count  # Thickness of each layer

    # Calculate the vertical position for this layer
    vertical_position = layer_index * layer_thickness

    # Create a cube at the specified position
    bpy.ops.mesh.primitive_cube_add(size=plate_dimension, location=(0, 0, vertical_position))
    layer = bpy.context.object

    # Scale the cube to make it a thin layer
    layer.scale[2] = layer_thickness / 2

    # Set the current layer as active
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    # Rotate the layer around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(layer_index * angle_per_layer), orient_axis='Z')

# Create the helical structure by calling the layer generation function
for index in range(layers_count):
    generate_layer(index)
