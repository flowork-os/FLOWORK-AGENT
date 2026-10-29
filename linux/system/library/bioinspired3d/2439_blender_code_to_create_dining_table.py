# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_to_create_dining_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code to create dining table.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

wood_texture = bpy.data.materials.new(name='WoodTexture')
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)

def add_tabletop():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
    top = bpy.context.object
    top.scale = (1.5, 1, 0.1)
    top.name = 'Tabletop'
    top.data.materials.append(wood_texture)
    return top

def add_leg(x, y, height, radius):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=(x, y, height / 2))
    leg = bpy.context.object
    leg.data.materials.append(wood_texture)
    return leg

add_tabletop()

height_of_legs = 1
radius_of_legs = 0.1

for i in range(4):
    leg_x = 1.4 * (i % 2) - 0.7
    leg_y = 0.9 * (i // 2) - 0.45
    add_leg(leg_x, leg_y, height_of_legs, radius_of_legs)


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
