# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_code__create_side_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender code, create side table.

import bpy

# Start by clearing the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood material for the table
wood_texture = bpy.data.materials.new(name='WoodTexture')
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to build the table
class Table:
    def __init__(self):
        self.create_table_top()
        self.create_legs()

    def create_table_top(self):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
        top_part = bpy.context.object
        top_part.name = 'TableTop'
        top_part.scale[2] = 0.1
        top_part.data.materials.append(wood_texture)

    def create_legs(self):
        for i in range(4):
            x_coord = 0.45 * (i % 2) - 0.225
            y_coord = 0.45 * (i // 2) - 0.225
            bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.5, location=(x_coord, y_coord, 0.25))
            leg_part = bpy.context.object
            leg_part.name = f'Leg_{i + 1}'
            leg_part.data.materials.append(wood_texture)

# Instantiate the table
Table()


# --- 3DCodeVerse geo variant: neutralize materials (auto-derived, do not edit) ---
import bpy as _bpy_geo
_geo_mat = _bpy_geo.data.materials.get("geo_neutral") or _bpy_geo.data.materials.new("geo_neutral")
try:
    _geo_mat.use_nodes = False
except Exception:
    pass
try:
    _geo_mat.diffuse_color = (0.8, 0.8, 0.8, 1.0)
except Exception:
    pass
for _geo_obj in list(_bpy_geo.data.objects):
    if _geo_obj.type == "MESH" and _geo_obj.data is not None:
        try:
            _geo_obj.data.materials.clear()
            _geo_obj.data.materials.append(_geo_mat)
        except Exception:
            pass
# --- end geo variant ---
