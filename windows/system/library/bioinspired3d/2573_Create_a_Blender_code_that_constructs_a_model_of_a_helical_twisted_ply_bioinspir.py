# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_Blender_code_that_constructs_a_model_of_a_helical_twisted_ply_bioinspir" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a Blender code that constructs a model of a helical twisted ply bioinspired structure Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_layers = 8  # Total layers
rotation_angle = 10  # Degrees of rotation per layer

def create_helical_layer(i):
    total_height = 2
    cube_size = 2
    thickness = total_height / num_layers

    z_pos = i * thickness

    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_pos))
    layer_object = bpy.context.object
    layer_object.scale[2] = thickness / 2

    bpy.context.view_layer.objects.active = layer_object
    layer_object.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(i * rotation_angle), orient_axis='Z')

for i in range(num_layers):
    create_helical_layer(i)
