# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_a_helical_twisted_ply_material_with_angular_variation_per_p" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of a helical twisted ply material with angular variation per ply in Blender Python script

import bpy
import math
import random

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical structure
layer_total = 15
rotation_angle = 4
apply_randomness = True
random_strength = 3

# Function to create a helical layer
def create_helical_layer(layer_index):
    height = 2
    size = 2
    thickness = height / layer_total
    z_position = layer_index * thickness

    # Add a cube
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = thickness / 2

    # Calculate rotation
    rotation = layer_index * rotation_angle
    if apply_randomness:
        rotation += random.uniform(-random_strength, random_strength)

    # Deselect and activate the layer
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    # Rotate the layer around Z
    bpy.ops.transform.rotate(value=math.radians(rotation), orient_axis='Z')

# Create the helical structure
for i in range(layer_total):
    create_helical_layer(i)
