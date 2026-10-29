# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_to_generate_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code to generate bookshelf

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create wood material
wood_material = bpy.data.materials.new(name='WoodTexture')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Shelf dimensions
shelf_dimensions = {'width': 2, 'height': 0.1, 'depth': 0.4, 'spacing': 0.5}
num_shelves = 5

# Generate shelves
for i in range(num_shelves):
    z_position = i * shelf_dimensions['spacing']
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    current_shelf = bpy.context.object
    current_shelf.scale = (shelf_dimensions['width'] / 2, shelf_dimensions['depth'] / 2, shelf_dimensions['height'] / 2)
    current_shelf.name = f'Shelf_{i + 1}'
    current_shelf.data.materials.append(wood_material)

# Create side panels
panel_thickness = 0.05
panel_height = num_shelves * shelf_dimensions['spacing']

for i in range(2):
    x_position = (shelf_dimensions['width'] / 2) * (1 - 2 * i)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, panel_height / 2))
    current_panel = bpy.context.object
    current_panel.scale = (panel_thickness / 2, shelf_dimensions['depth'] / 2, panel_height / 2)
    current_panel.name = f'Panel_{i + 1}'
    current_panel.data.materials.append(wood_material)


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
