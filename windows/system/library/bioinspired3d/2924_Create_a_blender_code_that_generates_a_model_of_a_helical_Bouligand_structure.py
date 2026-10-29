# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_blender_code_that_generates_a_model_of_a_helical_Bouligand_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a blender code that generates a model of a helical Bouligand structure.

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical model
layers = 12
angle_increment = 5

# Function to construct each layer of the helix

def construct_layer(index):
    height_of_structure = 2
    side_length = 2
    layer_height = height_of_structure / layers

    # Calculate vertical position
    z_coordinate = index * layer_height

    # Add a cube at the specified position
    bpy.ops.mesh.primitive_cube_add(size=side_length, location=(0, 0, z_coordinate))
    current_layer = bpy.context.object

    # Scale to a thin layer
    current_layer.scale[2] = layer_height / 2

    # Set current layer as active
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    # Rotate around Z-axis
    bpy.ops.transform.rotate(value=math.radians(index * angle_increment), orient_axis='Z')

# Create the helical model
for i in range(layers):
    construct_layer(i)
