# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_python_code__build_a_model_of_a_helical_twisted_ply_bioinspired_str" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender python code, build a model of a helical twisted ply bioinspired structure with angular variation per ply. think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
layer_count = 15  # Total number of layers
angle_increment = 20  # Degrees of rotation for each layer

# Noise parameters
randomize_rotation = True  # Toggle for rotation noise
max_angle_variation = 6  # Maximum angle variation in degrees

def generate_helical_structure(layer_index):
    # Function to create a layer of the helical structure.
    structure_height = 2
    cube_dimension = 2
    layer_height = structure_height / layer_count
    z_coord = layer_index * layer_height

    # Add a cube at the designated height
    bpy.ops.mesh.primitive_cube_add(size=cube_dimension, location=(0, 0, z_coord))
    helical_layer = bpy.context.object
    helical_layer.scale[2] = layer_height / 2

    # Determine the rotation angle with potential noise
    angle = layer_index * angle_increment
    if randomize_rotation:
        angle += random.uniform(-max_angle_variation, max_angle_variation)

    # Deselect all and select the current layer for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = helical_layer
    helical_layer.select_set(True)

    # Rotate the layer
    bpy.ops.transform.rotate(value=math.radians(angle), orient_axis='Z')
    return helical_layer

# Build the helical structure
for index in range(layer_count):
    generate_helical_structure(index)
