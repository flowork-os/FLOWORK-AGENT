# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_to_create_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code to create coffee table.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

brown_material = bpy.data.materials.new(name='Brown Material')
brown_material.diffuse_color = (0.55, 0.27, 0.07, 1)

class Table:
    def __init__(self):
        self.create_table_top()
        self.create_table_legs()

    def create_table_top(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.45))
        top = bpy.context.object
        top.scale = (1.5, 0.75, 0.1)
        top.name = 'Table Top'
        top.data.materials.append(brown_material)

    def create_table_legs(self):
        leg_height = 0.45
        leg_radius = 0.05
        leg_positions = [(-1.4, -0.7, leg_height / 2), (1.4, -0.7, leg_height / 2), (-1.4, 0.7, leg_height / 2), (1.4, 0.7, leg_height / 2)]
        for idx, pos in enumerate(leg_positions):
            bpy.ops.mesh.primitive_cylinder_add(radius=leg_radius, depth=leg_height, location=pos)
            leg = bpy.context.object
            leg.name = f'Leg {idx + 1}'
            leg.data.materials.append(brown_material)

my_table = Table()


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
