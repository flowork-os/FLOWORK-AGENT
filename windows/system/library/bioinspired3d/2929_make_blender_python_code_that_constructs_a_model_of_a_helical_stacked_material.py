# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_blender_python_code_that_constructs_a_model_of_a_helical_stacked_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make blender python code that constructs a model of a helical stacked material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the helical structure parameters
plies = 12  # total plies in the structure
rotation_step = 5  # rotation step in degrees

def create_helical_structure(plies, rotation_step):
    height = 2
    plate_dimension = 2
    thickness = height / plies

    for i in range(plies):
        z_position = i * thickness
        bpy.ops.mesh.primitive_cube_add(size=plate_dimension, location=(0, 0, z_position))
        plate = bpy.context.object
        plate.scale[2] = thickness / 2

        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(i * rotation_step), orient_axis='Z')

# Execute the creation of the helical structure
create_helical_structure(plies, rotation_step)
