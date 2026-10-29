# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_bookshelf_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of bookshelf using blender script

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

bookshelf_color = bpy.data.materials.new(name='WoodFinish')
bookshelf_color.diffuse_color = (0.55, 0.27, 0.07, 1)

def add_panel(position):
    bpy.ops.mesh.primitive_cube_add(size=2, location=position)
    panel = bpy.context.object
    panel.scale = (0.1, 1, 2)
    panel.data.materials.append(bookshelf_color)

add_panel((-1, 0, 1))
add_panel((1, 0, 1))

for shelf_index in range(3):
    z_coord = 0.5 + shelf_index * 1.0
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_coord))
    shelf = bpy.context.object
    shelf.scale = (1, 1, 0.1)
    shelf.data.materials.append(bookshelf_color)
    shelf.name = f'Shelf {shelf_index + 1}'


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
