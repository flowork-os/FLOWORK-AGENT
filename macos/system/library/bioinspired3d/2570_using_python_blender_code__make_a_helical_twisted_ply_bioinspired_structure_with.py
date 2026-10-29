# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_python_blender_code__make_a_helical_twisted_ply_bioinspired_structure_with" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using python blender code, make a helical twisted ply bioinspired structure with noise in each rotation.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical model parameters
ply_total = 9  # Number of plies
rotation_increment = 5  # Degrees of rotation for each ply
noise_toggle = True  # Enable noise
noise_degree = 3  # Maximum noise in degrees

# Function to create a helical plate
def create_helical_plate(index):
    height = 2
    cube_size = 2
    thickness = height / ply_total
    z_pos = index * thickness

    # Create the cube
    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_pos))
    plate = bpy.context.object
    plate.scale[2] = thickness / 2

    # Calculate rotation with noise
    base_rotation = index * rotation_increment
    if noise_toggle:
        base_rotation += random.uniform(-noise_degree, noise_degree)

    # Rotate the plate
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = plate
    plate.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(base_rotation), orient_axis='Z')

# Generate the helical structure
for i in range(ply_total):
    create_helical_plate(i)
