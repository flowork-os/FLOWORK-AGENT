# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_blender_code_that_makes_a_model_of_a_helical_twisted_ply_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create blender code that makes a model of a helical twisted ply material.

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the helical parameters
ply_count = 12  # Total number of plies
angle_increment = 5  # Rotation increment for each ply

# Function to construct the helical structure
def construct_helical():
    total_height = 2
    square_size = 2
    thickness = total_height / ply_count

    for index in range(ply_count):
        z_position = index * thickness
        bpy.ops.mesh.primitive_cube_add(size=square_size, location=(0, 0, z_position))
        current_plate = bpy.context.object
        current_plate.scale[2] = thickness / 2

        # Rotate the plate around the Z-axis
        bpy.context.view_layer.objects.active = current_plate
        current_plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(index * angle_increment), orient_axis='Z')

# Execute the construction function
construct_helical()
