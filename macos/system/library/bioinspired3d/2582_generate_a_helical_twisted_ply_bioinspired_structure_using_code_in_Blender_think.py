# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_helical_twisted_ply_bioinspired_structure_using_code_in_Blender_think" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a helical twisted ply bioinspired structure using code in Blender think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the spiral structure
layer_count = 9
rotation_increment = 20

def build_layer(index):
    height = 2
    size = 2
    thickness = height / layer_count

    z_position = index * thickness
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
    new_layer = bpy.context.object
    new_layer.scale[2] = thickness / 2

    bpy.context.view_layer.objects.active = new_layer
    new_layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(index * rotation_increment), orient_axis='Z')

# Create the spiral
for i in range(layer_count):
    build_layer(i)
