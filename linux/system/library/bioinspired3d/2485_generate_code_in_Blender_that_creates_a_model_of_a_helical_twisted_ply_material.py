# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_code_in_Blender_that_creates_a_model_of_a_helical_twisted_ply_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate code in Blender that creates a model of a helical twisted ply material.

import bpy
import math

# Remove all objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical structure parameters
layer_count = 15
rotation_increment = 8

def create_helical_structure():
    total_height = 2
    plate_size = 2
    thickness_per_layer = total_height / layer_count

    for i in range(layer_count):
        z_position = i * thickness_per_layer
        bpy.ops.mesh.primitive_cube_add(size=plate_size, location=(0, 0, z_position))
        current_layer = bpy.context.object
        current_layer.scale[2] = thickness_per_layer / 2
        bpy.context.view_layer.objects.active = current_layer
        current_layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(i * rotation_increment), orient_axis='Z')

create_helical_structure()
