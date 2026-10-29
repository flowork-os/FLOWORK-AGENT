# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_cube_and_place_small_spheres_at_each_of_its_corners_using_b" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of cube and place small spheres at each of its corners using blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.object

# Define the size of the spheres
sphere_radius = 0.1

# Create spheres at each corner of the cube
corners = [
    (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
    (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)
]

for corner in corners:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=sphere_radius, location=corner)

# Optionally, you can select all objects to see them together
bpy.ops.object.select_all(action='DESELECT')
cube.select_set(True)
for corner in corners:
    bpy.data.objects['Sphere'].select_set(True)
