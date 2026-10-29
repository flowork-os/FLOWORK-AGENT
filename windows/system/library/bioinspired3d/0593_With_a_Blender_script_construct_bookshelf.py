# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_script_construct_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender script construct bookshelf.

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the bookshelf
shelf_material = bpy.data.materials.new(name='Shelf Material')
shelf_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Brown wood color

# Parameters for shelves
shelf_thickness = 0.1
shelf_length = 0.5
shelf_depth = 0.2
shelf_count = 5
shelf_spacing = 0.4

# Function to add shelves
for shelf_index in range(shelf_count):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, shelf_index * shelf_spacing))
    current_shelf = bpy.context.object
    current_shelf.scale = (shelf_length / 2, shelf_depth / 2, shelf_thickness / 2)
    current_shelf.name = f'Shelf {shelf_index + 1}'
    current_shelf.data.materials.append(shelf_material)

# Function to add side panels
panel_width = 0.05
panel_total_height = shelf_count * shelf_spacing

for panel_index in range(2):
    x_position = (shelf_length / 2) * (panel_index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, panel_total_height / 2))
    side_panel_object = bpy.context.object
    side_panel_object.scale = (panel_width / 2, shelf_depth / 2, panel_total_height / 2)
    side_panel_object.name = f'Side Panel {panel_index + 1}'
    side_panel_object.data.materials.append(shelf_material)


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
