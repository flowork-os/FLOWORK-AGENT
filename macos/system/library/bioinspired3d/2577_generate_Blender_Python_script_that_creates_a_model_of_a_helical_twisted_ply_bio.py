# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_Python_script_that_creates_a_model_of_a_helical_twisted_ply_bio" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender Python script that creates a model of a helical twisted ply bioinspired structure. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
num_plates = 6  # number of plates in the helical design
rotation_per_plate = 8  # degrees of rotation for each plate

def construct_plate(index):
    overall_height = 2
    plate_dimension = 2
    thickness_of_plate = overall_height / num_plates

    vertical_position = index * thickness_of_plate
    bpy.ops.mesh.primitive_cube_add(size=plate_dimension, location=(0, 0, vertical_position))
    plate = bpy.context.object
    plate.scale[2] = thickness_of_plate / 2

    bpy.context.view_layer.objects.active = plate
    plate.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(index * rotation_per_plate), orient_axis='Z')

# Generate the helical design
for i in range(num_plates):
    construct_plate(i)
