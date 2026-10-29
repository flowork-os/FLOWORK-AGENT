# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_bookshelf_using_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of bookshelf using a Blender script

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the shelves
shelf_material = bpy.data.materials.new(name="ShelfMaterial")
shelf_material.diffuse_color = (0.54, 0.26, 0.06, 1)  # Brown color for shelves

# Parameters for shelves
shelf_dimensions = (2, 0.1, 0.4)
shelf_gap = 0.6
shelf_count = 5

# Function to create shelves
def create_shelves(count, gap, dimensions, material):
    for index in range(count):
        position_z = index * gap
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, position_z))
        shelf = bpy.context.object
        shelf.scale = (dimensions[0] / 2, dimensions[2] / 2, dimensions[1] / 2)
        shelf.name = f"Shelf_{index + 1}"
        shelf.data.materials.append(material)

create_shelves(shelf_count, shelf_gap, shelf_dimensions, shelf_material)

# Create side panels
panel_thickness = 0.05
panel_height = shelf_count * shelf_gap

for index in range(2):
    position_x = (shelf_dimensions[0] / 2) * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(position_x, 0, panel_height / 2))
    side_panel = bpy.context.object
    side_panel.scale = (panel_thickness / 2, shelf_dimensions[2] / 2, panel_height / 2)
    side_panel.name = f"SidePanel_{index + 1}"
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
