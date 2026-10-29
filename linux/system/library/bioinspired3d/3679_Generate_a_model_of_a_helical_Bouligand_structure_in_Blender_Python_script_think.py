# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_a_helical_Bouligand_structure_in_Blender_Python_script_think" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of a helical Bouligand structure in Blender Python script think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for helical structure
num_plates = 12
rotation_step = 5

def create_helical_structure(count, rotation):
    total_height = 2
    plate_size = 2
    thickness = total_height / count

    for idx in range(count):
        z_position = idx * thickness
        bpy.ops.mesh.primitive_cube_add(size=plate_size, location=(0, 0, z_position))
        plate = bpy.context.object
        plate.scale[2] = thickness / 2
        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(idx * rotation), orient_axis='Z')

# Create the helical structure
create_helical_structure(num_plates, rotation_step)
