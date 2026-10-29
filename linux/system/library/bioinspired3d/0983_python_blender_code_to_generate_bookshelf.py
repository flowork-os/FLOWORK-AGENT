# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_generate_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to generate bookshelf.

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a wood material with a specific color
shelf_material = bpy.data.materials.new(name='ShelfMaterial')
shelf_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Dark brown

# Create shelves using a loop
for shelf_index in range(5):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, shelf_index * 0.6))
    current_shelf = bpy.context.object
    current_shelf.scale = (1, 0.2, 0.05)
    current_shelf.name = f'Shelf_{shelf_index + 1}'
    current_shelf.data.materials.append(shelf_material)

# Create side panels
panel_height = 3.0
panel_thickness = 0.05
for side_index in range(2):
    x_position = (1 * (side_index * 2 - 1))
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, panel_height / 2))
    side_panel = bpy.context.object
    side_panel.scale = (panel_thickness / 2, 0.2, panel_height / 2)
    side_panel.name = f'SidePanel_{side_index + 1}'
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
