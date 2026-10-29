# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_python_code_that_constructs_cube_and_place_small_spheres_at_each_o" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender python code that constructs cube and place small spheres at each of its corners

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.active_object

# Get the cube's dimensions and calculate corner positions
half_size = cube.dimensions.x / 2
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
