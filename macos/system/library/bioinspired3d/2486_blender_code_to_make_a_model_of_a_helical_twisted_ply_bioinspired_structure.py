# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_to_make_a_model_of_a_helical_twisted_ply_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code to make a model of a helical twisted ply bioinspired structure

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
ply_count = 7  # Number of plies
rotation_angle = 5  # Rotation angle for each ply

def create_helical_layer(index):
    total_height = 2
    plate_side = 2
    layer_thickness = total_height / ply_count

    z_position = index * layer_thickness
    bpy.ops.mesh.primitive_cube_add(size=plate_side, location=(0, 0, z_position))
    helical_layer = bpy.context.object
    helical_layer.scale[2] = layer_thickness / 2

    bpy.context.view_layer.objects.active = helical_layer
    helical_layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(index * rotation_angle), orient_axis='Z')

# Generate the helical structure
for i in range(ply_count):
    create_helical_layer(i)
