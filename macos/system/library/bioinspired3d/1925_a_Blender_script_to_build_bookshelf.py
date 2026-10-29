# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_to_build_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script to build bookshelf.

import bpy

# Clear the current scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood-like material
shelf_material = bpy.data.materials.new(name="Shelf Material")
shelf_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to create a shelf
def create_shelf(index, width, height, depth, spacing):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * spacing))
    shelf = bpy.context.object
    shelf.scale = (width / 2, depth / 2, height / 2)
    shelf.name = f"Shelf {index + 1}"
    shelf.data.materials.append(shelf_material)

# Create multiple shelves
shelf_width = 2
shelf_height = 0.1
shelf_depth = 0.4
shelf_spacing = 0.5
num_of_shelves = 5

for i in range(num_of_shelves):
    create_shelf(i, shelf_width, shelf_height, shelf_depth, shelf_spacing)

# Create side panels
panel_thickness = 0.05
panel_height = num_of_shelves * shelf_spacing

for i in range(2):
    x_location = (shelf_width / 2) * (i * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_location, 0, panel_height / 2))
    side_panel = bpy.context.object
    side_panel.scale = (panel_thickness / 2, shelf_depth / 2, panel_height / 2)
    side_panel.name = f"Side Panel {i + 1}"
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
