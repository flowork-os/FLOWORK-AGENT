# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_blender_python_code_that_constructs_a_helical_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create blender python code that constructs a helical bioinspired structure

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure settings
layer_count = 12
rotation_step = 8

def add_plate(plate_index):
    structure_height = 2
    cube_size = 2
    thickness_of_plate = structure_height / layer_count

    # Calculate z-position for the current plate
    z_position = plate_index * thickness_of_plate

    # Add a cube to the scene
    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
    plate = bpy.context.object

    # Scale the cube to create a thin plate
    plate.scale[2] = thickness_of_plate / 2

    # Make the plate active
    bpy.context.view_layer.objects.active = plate
    plate.select_set(True)

    # Rotate around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(plate_index * rotation_step), orient_axis='Z')

# Create the helical structure
for i in range(layer_count):
    add_plate(i)
