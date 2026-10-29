# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_script__generate_a_helical_Bouligand_bioinspired_material__think_st" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender script, generate a helical Bouligand bioinspired material. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

ply_count = 6
angle_per_ply = 20

def construct_helical_layers():
    structure_height = 2
    layer_size = 2
    individual_thickness = structure_height / ply_count

    for layer_index in range(ply_count):
        layer_z_position = layer_index * individual_thickness
        bpy.ops.mesh.primitive_cube_add(size=layer_size, location=(0, 0, layer_z_position))
        layer_object = bpy.context.object
        layer_object.scale[2] = individual_thickness / 2
        bpy.context.view_layer.objects.active = layer_object
        layer_object.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(layer_index * angle_per_ply), orient_axis='Z')

construct_helical_layers()
