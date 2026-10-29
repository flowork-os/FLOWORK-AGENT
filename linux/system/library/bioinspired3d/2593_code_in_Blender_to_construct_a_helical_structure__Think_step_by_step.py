# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_to_construct_a_helical_structure__Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender to construct a helical structure. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical structure parameters
num_layers = 12  # Number of layers
angle_per_layer = 10  # Rotation angle

def create_helical_structure(layer_count, rotation_angle):
    total_height = 2
    plate_size = 2
    layer_thickness = total_height / layer_count

    for i in range(layer_count):
        z_position = i * layer_thickness
        bpy.ops.mesh.primitive_cube_add(size=plate_size, location=(0, 0, z_position))
        plate = bpy.context.object
        plate.scale[2] = layer_thickness / 2
        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(i * rotation_angle), orient_axis='Z')

create_helical_structure(num_layers, angle_per_layer)
