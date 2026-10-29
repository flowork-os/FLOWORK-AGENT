# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_cube_and_place_small_spheres_at_each_of_its_corners_using_blender_python_c" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build cube and place small spheres at each of its corners using blender python code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.object

# Define the size of the spheres
sphere_radius = 0.1

# Calculate the corners of the cube
corners = [
    (1, 1, 1),
    (1, 1, -1),
    (1, -1, 1),
    (1, -1, -1),
    (-1, 1, 1),
    (-1, 1, -1),
    (-1, -1, 1),
    (-1, -1, -1)
]

# Create spheres at each corner
for corner in corners:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=sphere_radius, location=corner)
