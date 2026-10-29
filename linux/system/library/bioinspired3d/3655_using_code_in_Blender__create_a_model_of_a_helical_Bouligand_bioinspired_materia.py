# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_code_in_Blender__create_a_model_of_a_helical_Bouligand_bioinspired_materia" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using code in Blender, create a model of a helical Bouligand bioinspired material think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure configuration
layer_count = 9  # Number of layers
angle_increment = 20  # Rotation angle for each layer

def add_layer(index):
    total_height = 2
    square_size = 2
    layer_height = total_height / layer_count

    # Calculate the Z-axis position for the current layer
    z_axis = index * layer_height

    # Create a cube at the calculated Z position
    bpy.ops.mesh.primitive_cube_add(size=square_size, location=(0, 0, z_axis))
    layer_cube = bpy.context.object

    # Scale the cube to form a thin layer
    layer_cube.scale[2] = layer_height / 2

    # Rotate the layer around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(index * angle_increment), orient_axis='Z')

# Generate the helical structure
for i in range(layer_count):
    add_layer(i)
