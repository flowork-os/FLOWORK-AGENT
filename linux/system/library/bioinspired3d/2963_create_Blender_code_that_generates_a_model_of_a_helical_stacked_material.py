# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_Blender_code_that_generates_a_model_of_a_helical_stacked_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create Blender code that generates a model of a helical stacked material.

import bpy
import math

# Start with a clean slate
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helix parameters
layer_count = 9  # Number of layers
rotation_increment = 8  # Rotation in degrees for each layer

def create_helical_structure(layers):
    for layer_index in range(layers):
        create_single_layer(layer_index)

def create_single_layer(index):
    height = 2
    size = 2
    thickness = height / layer_count
    z_position = index * thickness

    bpy.ops.mesh.primitive_cube_add(
        size=size,
        location=(0, 0, z_position)
    )
    layer = bpy.context.object
    layer.scale[2] = thickness / 2
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)
    bpy.ops.transform.rotate(
        value=math.radians(index * rotation_increment),
        orient_axis='Z'
    )

# Execute the creation of the helical structure
create_helical_structure(layer_count)
