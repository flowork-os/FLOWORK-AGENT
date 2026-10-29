# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_bookshelf_using_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build bookshelf using python blender code

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a new material for the shelves
wooden_surface = bpy.data.materials.new(name='WoodSurface')
wooden_surface.diffuse_color = (0.5, 0.25, 0.05, 1)  # Darker wood color

# Shelf specifications
shelf_height = 0.1
shelf_depth = 0.4
shelf_width = 0.6
spacing_between_shelves = 0.5
shelf_count = 4

# Create shelves using a loop
for index in range(shelf_count):
    z_position = index * spacing_between_shelves
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    shelf = bpy.context.object
    shelf.scale = (shelf_width / 2, shelf_depth / 2, shelf_height / 2)
    shelf.name = f'Shelf_{index + 1}'
    shelf.data.materials.append(wooden_surface)

# Panel specifications
panel_thickness = 0.05
panel_height = shelf_count * spacing_between_shelves

# Create side panels
for index in range(2):
    x_position = shelf_width / 2 * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, panel_height / 2))
    panel = bpy.context.object
    panel.scale = (panel_thickness / 2, shelf_depth / 2, panel_height / 2)
    panel.name = f'Panel_{index + 1}'
    panel.data.materials.append(wooden_surface)


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
