# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_3x3x3_grid_of_cylinders_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct 3x3x3 grid of cylinders using blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the grid
rows = 3
cols = 3
layers = 3
spacing = 2

# Create a 3x3x3 grid of cylinders
for z in range(layers):
    for y in range(rows):
        for x in range(cols):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1, location=(x * spacing, y * spacing, z * spacing))
