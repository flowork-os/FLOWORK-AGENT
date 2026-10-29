# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_code_in_Blender_that_builds_a_helical_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create code in Blender that builds a helical bioinspired structure.

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure configuration
layers = 6
rotation_deg = 18

def generate_helical_structure(num_layers, rotation):
    height = 2
    size = 2
    thickness = height / num_layers

    for i in range(num_layers):
        z_pos = i * thickness
        bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_pos))
        layer = bpy.context.object
        layer.scale[2] = thickness / 2
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(i * rotation), orient_axis='Z')

generate_helical_structure(layers, rotation_deg)
