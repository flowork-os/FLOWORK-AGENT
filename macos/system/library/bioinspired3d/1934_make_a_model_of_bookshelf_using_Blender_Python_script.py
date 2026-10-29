# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_bookshelf_using_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of bookshelf using Blender Python script

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

shelf_material = bpy.data.materials.new(name='ShelfMaterial')
shelf_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Wood-like color

WIDTH = 2
HEIGHT = 0.1
DEPTH = 0.4
SPACE = 0.5
SHELF_COUNT = 5

for i in range(SHELF_COUNT):
    z_position = i * SPACE
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    shelf = bpy.context.object
    shelf.scale = (WIDTH / 2, DEPTH / 2, HEIGHT / 2)
    shelf.name = f'Shelf_{i + 1}'
    shelf.data.materials.append(shelf_material)

PANEL_THICKNESS = 0.05
PANEL_HEIGHT = SHELF_COUNT * SPACE

for i in range(2):
    x_position = (WIDTH / 2) * (i * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, PANEL_HEIGHT / 2))
    side_panel = bpy.context.object
    side_panel.scale = (PANEL_THICKNESS / 2, DEPTH / 2, PANEL_HEIGHT / 2)
    side_panel.name = f'SidePanel_{i + 1}'
    side_panel.data.materials.append(shelf_material)


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
