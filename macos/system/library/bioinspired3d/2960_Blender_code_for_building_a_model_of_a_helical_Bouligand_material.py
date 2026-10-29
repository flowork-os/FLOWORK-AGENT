# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_for_building_a_model_of_a_helical_Bouligand_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code for building a model of a helical Bouligand material.

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical structure parameters
number_of_layers = 12
rotation_degrees = 5

def make_helical_structure(count, rotation):
    total_height = 2
    plate_side = 2
    thickness_of_layer = total_height / count

    for i in range(count):
        z_position = i * thickness_of_layer
        bpy.ops.mesh.primitive_cube_add(size=plate_side, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = thickness_of_layer / 2
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(i * rotation), orient_axis='Z')

# Create the helical structure
make_helical_structure(number_of_layers, rotation_degrees)
