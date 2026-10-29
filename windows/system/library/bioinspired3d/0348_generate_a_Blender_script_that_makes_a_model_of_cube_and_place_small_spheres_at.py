# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_Blender_script_that_makes_a_model_of_cube_and_place_small_spheres_at" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a Blender script that makes a model of cube and place small spheres at each of its corners.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.active_object

# Get the dimensions of the cube
half_size = cube.dimensions.x / 2

# Define the positions for the spheres at each corner of the cube
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

# Create spheres at each corner
for corner in corners:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=corner)
