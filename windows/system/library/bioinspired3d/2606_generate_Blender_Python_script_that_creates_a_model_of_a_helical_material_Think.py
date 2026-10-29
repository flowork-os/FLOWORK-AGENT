# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_Python_script_that_creates_a_model_of_a_helical_material_Think" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender Python script that creates a model of a helical material Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
layers_count = 10  # Number of layers in the structure
rotation_angle = 10  # Degrees of rotation for each layer

def generate_layer(layer_index):
    # Function to create a single layer of the helical design.
    height_of_structure = 2
    square_size = 2
    layer_thickness = height_of_structure / layers_count

    # Determine the vertical position of the layer
    z_position = layer_index * layer_thickness

    # Add a cube at the specified location
    bpy.ops.mesh.primitive_cube_add(
        size=square_size,
        location=(0, 0, z_position)
    )

    created_layer = bpy.context.object

    # Scale the cube to make it a thin layer
    created_layer.scale[2] = layer_thickness / 2

    # Set the layer as the active object
    bpy.context.view_layer.objects.active = created_layer
    created_layer.select_set(True)

    # Rotate the layer around the Z-axis
    bpy.ops.transform.rotate(
        value=math.radians(layer_index * rotation_angle),
        orient_axis='Z'
    )

    return created_layer

# Create the helical structure by looping through the layers
for index in range(layers_count):
    generate_layer(index)
