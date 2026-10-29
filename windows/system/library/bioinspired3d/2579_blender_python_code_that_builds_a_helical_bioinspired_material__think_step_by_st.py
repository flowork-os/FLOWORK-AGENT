# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_builds_a_helical_bioinspired_material__think_step_by_st" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that builds a helical bioinspired material. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
layers_count = 10  # Total layers in the structure
angle_increment = 15  # Degrees of rotation for each layer

def generate_layer(layer_index):
    # Function to create a single layer for the helical design.
    height_of_structure = 2  # Overall height of the structure
    base_size = 2  # Dimensions of each square layer
    layer_thickness = height_of_structure / layers_count  # Thickness of each layer

    # Calculate vertical position for the layer
    vertical_position = layer_index * layer_thickness

    # Add a cube at the specified position
    bpy.ops.mesh.primitive_cube_add(size=base_size, location=(0, 0, vertical_position))

    current_layer = bpy.context.object

    # Scale the cube to form a thin layer
    current_layer.scale[2] = layer_thickness / 2

    # Set the layer as the active object
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    # Rotate the layer around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(layer_index * angle_increment), orient_axis='Z')

    return current_layer

# Create the helical structure by looping through the number of layers
for idx in range(layers_count):
    generate_layer(idx)
