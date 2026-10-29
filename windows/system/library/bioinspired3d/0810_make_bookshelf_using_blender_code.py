# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_bookshelf_using_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make bookshelf using blender code

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the shelves
shelf_material = bpy.data.materials.new(name="ShelfColor")
shelf_material.diffuse_color = (0.5, 0.25, 0.05, 1)  # Darker wood color

# Define shelf parameters
width = 2.0
height = 0.1
depth = 0.4
spacing = 0.6
shelves = 5

# Function to build shelves
def build_shelves(num_shelves, spacing, width, height, depth, material):
    for index in range(num_shelves):
        z_coord = index * spacing
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_coord))
        new_shelf = bpy.context.object
        new_shelf.scale = (width / 2, depth / 2, height / 2)
        new_shelf.name = f"Shelf_{index + 1}"
        new_shelf.data.materials.append(material)

build_shelves(shelves, spacing, width, height, depth, shelf_material)

# Function to create side panels
panel_thickness = 0.05
panel_height = shelves * spacing

for i in range(2):
    x_coord = (width / 2) * (i * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_coord, 0, panel_height / 2))
    side_panel = bpy.context.object
    side_panel.scale = (panel_thickness / 2, depth / 2, panel_height / 2)
    side_panel.name = f"SidePanel_{i + 1}"
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
