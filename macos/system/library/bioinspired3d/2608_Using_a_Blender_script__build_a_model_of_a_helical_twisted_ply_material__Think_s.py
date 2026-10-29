# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_a_Blender_script__build_a_model_of_a_helical_twisted_ply_material__Think_s" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using a Blender script, build a model of a helical twisted ply material. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

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

create_helical_structure(layer_count)
