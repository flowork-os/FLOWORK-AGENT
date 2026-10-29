# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_script_generate_a_helical_twisted_ply_material_with_rotational_noi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender script generate a helical twisted ply material with rotational noise.

import bpy
import math
import random

# Clear the current scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
layers = 15
rotation_increment = 3
noise_active = True
noise_range = 8

def build_helical_structure(num_layers):
    for layer_index in range(num_layers):
        create_helical_plate(layer_index)

def create_helical_plate(index):
    height = 2
    cube_size = 2
    thickness = height / layers
    z_position = index * thickness

    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
    plate = bpy.context.object
    plate.scale[2] = thickness / 2

    base_rotation = index * rotation_increment
    if noise_active:
        base_rotation += random.uniform(-noise_range, noise_range)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = plate
    plate.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(base_rotation), orient_axis='Z')

# Execute the building process
build_helical_structure(layers)
