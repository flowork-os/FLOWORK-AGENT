# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_that_makes_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code that makes a model of bookshelf.

import bpy

# Start by clearing the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the shelves
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.6, 0.3, 0.1, 1)  # Different shade of wood color

# Shelf parameters
shelf_height = 0.1
shelf_depth = 0.4
shelf_width = 0.6
shelf_spacing = 0.5
num_shelves = 4

# Create shelves
for i in range(num_shelves):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, i * shelf_spacing))
    shelf = bpy.context.object
    shelf.scale = (shelf_width / 2, shelf_depth / 2, shelf_height / 2)
    shelf.name = f'Shelf_{i + 1}'
    shelf.data.materials.append(wood_material)

# Side panel dimensions
panel_thickness = 0.05
panel_height = num_shelves * shelf_spacing

# Create side panels
for j in range(2):
    bpy.ops.mesh.primitive_cube_add(size=2, location=((shelf_width / 2) * (j * 2 - 1), 0, panel_height / 2))
    side_panel = bpy.context.object
    side_panel.scale = (panel_thickness / 2, shelf_depth / 2, panel_height / 2)
    side_panel.name = f'Side_Panel_{j + 1}'
    side_panel.data.materials.append(wood_material)


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
