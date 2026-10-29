# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_to_make_a_model_of_a_helical_twisted_ply_bioinspired_structure__t" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code to make a model of a helical twisted ply bioinspired structure. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_total = 9  # Number of layers
rotation_step = 20  # Degree of rotation for each layer

def create_helical_layers(total_layers, rotation_step):
    height = 2
    size = 2
    layer_thickness = height / total_layers

    for i in range(total_layers):
        z_pos = i * layer_thickness
        bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_pos))
        layer = bpy.context.object
        layer.scale[2] = layer_thickness / 2

        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(i * rotation_step), orient_axis='Z')

create_helical_layers(layer_total, rotation_step)
