# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_code__create_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender code, create bookshelf

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define parameters for the shelf
shelf_w = 1.0
shelf_h = 0.1
shelf_d = 0.5
shelf_l = 3.0
spacing_between = 1.0
shelves_total = 4
height_total = shelves_total * spacing_between

# Create a new material for the wood
wood_material = bpy.data.materials.new(name="WoodMaterial")
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to add shelves
def add_shelf(shelf_index):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, shelf_index * spacing_between))
    new_shelf = bpy.context.object
    new_shelf.scale = (shelf_l / 2, shelf_d / 2, shelf_h / 2)
    new_shelf.name = f"Shelf_{shelf_index + 1}"
    new_shelf.data.materials.append(wood_material)

# Create all shelves
for i in range(shelves_total):
    add_shelf(i)

# Function to create side panels
def add_side_panel(side_index):
    x_pos = (shelf_l / 2) * (side_index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_pos, 0, height_total / 2))
    side_panel = bpy.context.object
    side_panel.scale = (0.05, shelf_d / 2, height_total / 2)
    side_panel.name = f"SidePanel_{side_index + 1}"
    side_panel.data.materials.append(wood_material)

# Create side panels
for i in range(2):
    add_side_panel(i)


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
