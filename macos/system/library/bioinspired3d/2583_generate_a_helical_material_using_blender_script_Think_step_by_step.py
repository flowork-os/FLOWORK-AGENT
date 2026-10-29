# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_helical_material_using_blender_script_Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a helical material using blender script Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Spiral structure settings
ply_total = 6
angle_change = 12

def make_layer(layer_idx):
    structure_height = 2
    square_size = 2
    individual_thickness = structure_height / ply_total

    z_pos = layer_idx * individual_thickness
    bpy.ops.mesh.primitive_cube_add(size=square_size, location=(0, 0, z_pos))
    created_layer = bpy.context.object
    created_layer.scale[2] = individual_thickness / 2

    bpy.context.view_layer.objects.active = created_layer
    created_layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(layer_idx * angle_change), orient_axis='Z')

# Generate the spiral structure
for idx in range(ply_total):
    make_layer(idx)
