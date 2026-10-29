# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_bookshelf_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make bookshelf in a blender code

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_wood = bpy.data.materials.new(name='WoodTexture')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)

shelf_dimensions = {'width': 0.5, 'height': 0.1, 'depth': 0.2}
spacing_between_shelves = 0.4
shelves_total = 3

for index in range(shelves_total):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * spacing_between_shelves))
    current_shelf = bpy.context.object
    current_shelf.scale = (shelf_dimensions['width'] / 2, shelf_dimensions['depth'] / 2, shelf_dimensions['height'] / 2)
    current_shelf.name = f'Shelf_{index + 1}'
    current_shelf.data.materials.append(material_wood)

panel_height = shelves_total * spacing_between_shelves

for index in range(2):
    position_x = shelf_dimensions['width'] / 2 * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(position_x, 0, panel_height / 2 - shelf_dimensions['height'] / 2))
    side_panel = bpy.context.object
    side_panel.scale = (0.025, shelf_dimensions['depth'] / 2, panel_height / 2)
    side_panel.name = f'SidePanel_{index + 1}'
    side_panel.data.materials.append(material_wood)


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
