# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_script__generate_a_helical_twisted_ply_bioinspired_material_Think_s" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender script, generate a helical twisted ply bioinspired material Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for creating a helical form
layers_count = 10  # total number of layers
angle_per_layer = 15  # degrees of rotation for each layer

def generate_layer(layer_index):
    # Function to create a single layer of the helix
    height_of_structure = 2
    layer_size = 2
    thickness_of_layer = height_of_structure / layers_count

    # Determine the Z position for the layer
    z_position = layer_index * thickness_of_layer

    # Add a cube at the calculated position
    bpy.ops.mesh.primitive_cube_add(size=layer_size, location=(0, 0, z_position))
    layer = bpy.context.object

    # Scale the cube to form a thin layer
    layer.scale[2] = thickness_of_layer / 2

    # Set the layer as active and selected
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    # Rotate around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(layer_index * angle_per_layer), orient_axis='Z')

    return layer

# Create the helical structure by looping through the layers
for index in range(layers_count):
    generate_layer(index)
