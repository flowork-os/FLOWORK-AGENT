# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_Blender_script__make_cube_and_place_small_spheres_at_each_of_its_corners" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a Blender script, make cube and place small spheres at each of its corners

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.object

# Get the dimensions of the cube
half_size = cube.dimensions.x / 2

# Define the positions for the corners of the cube
corners = [
    (half_size, half_size, half_size),
    (half_size, half_size, -half_size),
    (half_size, -half_size, half_size),
    (half_size, -half_size, -half_size),
    (-half_size, half_size, half_size),
    (-half_size, half_size, -half_size),
    (-half_size, -half_size, half_size),
    (-half_size, -half_size, -half_size),
]

# Create small spheres at each corner
for corner in corners:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=corner)
