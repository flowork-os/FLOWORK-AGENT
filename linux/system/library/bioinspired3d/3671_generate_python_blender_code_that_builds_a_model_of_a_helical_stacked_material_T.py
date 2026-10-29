# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_python_blender_code_that_builds_a_model_of_a_helical_stacked_material_T" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate python blender code that builds a model of a helical stacked material Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical formation
layers_count = 10  # Total number of layers in the structure
angle_increment = 15  # Degrees of rotation for each layer

# Function to generate a layer in the helical structure
def generate_layer(layer_index):
    height_of_structure = 2  # Overall height
    plate_dimension = 2  # Size of each square layer
    layer_thickness = height_of_structure / layers_count  # Thickness of each layer

    # Determine the vertical position of the layer
    vertical_position = layer_index * layer_thickness

    # Add a cube at the specified position
    bpy.ops.mesh.primitive_cube_add(
        size=plate_dimension,
        location=(0, 0, vertical_position)
    )

    current_layer = bpy.context.object

    # Scale the cube to make it a thin layer
    current_layer.scale[2] = layer_thickness / 2

    # Set the layer as the active object
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
