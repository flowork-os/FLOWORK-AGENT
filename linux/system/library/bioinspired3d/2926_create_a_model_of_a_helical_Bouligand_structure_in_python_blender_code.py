# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_a_helical_Bouligand_structure_in_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of a helical Bouligand structure in python blender code

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical model parameters
layer_count = 15
rotation_angle = 12

def generate_helical_structure(layer_count, rotation_angle):
    height_of_structure = 2
    cube_size = 2
    thickness_per_layer = height_of_structure / layer_count

    for i in range(layer_count):
        z_position = i * thickness_per_layer
        bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
        current_cube = bpy.context.object
        current_cube.scale[2] = thickness_per_layer / 2
        bpy.context.view_layer.objects.active = current_cube
        current_cube.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(i * rotation_angle), orient_axis='Z')

# Generate the helical structure
generate_helical_structure(layer_count, rotation_angle)
