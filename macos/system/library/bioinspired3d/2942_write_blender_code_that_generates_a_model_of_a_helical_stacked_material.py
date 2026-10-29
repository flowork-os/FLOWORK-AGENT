# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_code_that_generates_a_model_of_a_helical_stacked_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender code that generates a model of a helical stacked material

import bpy
import math

# Remove all objects from the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the helical structure parameters
ply_count = 8
rotation_increment = 5

def create_helical_plates(count, rotation):
    height = 2
    plate_side = 2
    thickness = height / count

    for i in range(count):
        z_position = i * thickness
        bpy.ops.mesh.primitive_cube_add(size=plate_side, location=(0, 0, z_position))
        plate = bpy.context.object
        plate.scale[2] = thickness / 2
        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(i * rotation), orient_axis='Z')

create_helical_plates(ply_count, rotation_increment)
