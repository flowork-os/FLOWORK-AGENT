# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_script_build_a_model_of_cube_and_place_small_spheres_at_each" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender script build a model of cube and place small spheres at each of its corners.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.object

# Get the cube's dimensions
half_size = cube.dimensions.x / 2

# Define the corner positions for the spheres
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
