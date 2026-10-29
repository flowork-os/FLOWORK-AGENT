# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_creating_wallpaper_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for creating wallpaper pattern.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

radius = 1.2
height = 0.1
rows_count = 5
columns_count = 5

def create_single_hexagon(x_pos, y_pos, z_pos):
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=radius, depth=height, location=(x_pos, y_pos, z_pos))

for r in range(rows_count):
    for c in range(columns_count):
        x_coord = c * 1.5 * radius
        y_coord = r * math.sqrt(3) * radius + (c % 2) * (math.sqrt(3) / 2 * radius)
        create_single_hexagon(x_coord, y_coord, 0)
