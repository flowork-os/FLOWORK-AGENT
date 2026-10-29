# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_code_in_Blender_create_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using code in Blender create bookshelf

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize wood material for the bookshelf
bookshelf_material = bpy.data.materials.new(name='Bookshelf Wood')
bookshelf_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Brown color for wood

# Create shelves with specified dimensions
shelf_count = 5
shelf_height = 0.1
shelf_width = 0.5
shelf_depth = 0.2
shelf_gap = 0.4

# Generate shelves
for idx in range(shelf_count):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, idx * shelf_gap))
    shelf = bpy.context.object
    shelf.scale = (shelf_width / 2, shelf_depth / 2, shelf_height / 2)
    shelf.name = f'Shelf {idx + 1}'
    shelf.data.materials.append(bookshelf_material)

# Create side panels
panel_width = 0.05
panel_full_height = shelf_count * shelf_gap

for j in range(2):
    x_position = (shelf_width / 2) * (j * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, panel_full_height / 2))
    side_panel = bpy.context.object
    side_panel.scale = (panel_width / 2, shelf_depth / 2, panel_full_height / 2)
    side_panel.name = f'Side Panel {j + 1}'
    side_panel.data.materials.append(bookshelf_material)


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
