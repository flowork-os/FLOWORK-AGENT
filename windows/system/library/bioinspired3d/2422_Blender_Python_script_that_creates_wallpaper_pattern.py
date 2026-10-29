# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_creates_wallpaper_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that creates wallpaper pattern

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

radius_of_hex = 1
height_of_hex = 0.1
number_of_rows = 5
number_of_columns = 5

def generate_hexagon(x_pos, y_pos, z_pos):
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=radius_of_hex, depth=height_of_hex, location=(x_pos, y_pos, z_pos))
    return bpy.context.object

for row_index in range(number_of_rows):
    for col_index in range(number_of_columns):
        x_coord = col_index * 1.5 * radius_of_hex
        y_coord = row_index * math.sqrt(3) * radius_of_hex + (col_index % 2) * (math.sqrt(3) / 2 * radius_of_hex)
        generate_hexagon(x_coord, y_coord, 0)
