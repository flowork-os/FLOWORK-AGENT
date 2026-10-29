# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_a_helical_Bouligand_material_with_angular_variation_per_ply" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of a helical Bouligand material with angular variation per ply in blender python code

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure settings
layer_count = 15
rotation_angle = 20
enable_noise = True
max_noise = 6

def create_helical_structure(count, rotation, noise):
    for i in range(count):
        z_position = (i * 2) / count
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
        cube = bpy.context.object
        cube.scale[2] = (2 / count) / 2

        angle = i * rotation
        if enable_noise:
            angle += random.uniform(-noise, noise)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = cube
        cube.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(angle), orient_axis='Z')

create_helical_structure(layer_count, rotation_angle, max_noise)
