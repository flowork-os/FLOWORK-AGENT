# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_Blender_code_that_makes_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a Blender code that makes bookshelf

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

wooden_material = bpy.data.materials.new(name="WoodenFinish")
wooden_material.diffuse_color = (0.6, 0.3, 0.1, 1)  # A different shade of wood

shelf_width = 2.0
shelf_height = 0.1
shelf_depth = 0.4
spacing_between_shelves = 0.6
number_of_shelves = 5

def generate_shelves(total_shelves, spacing, width, height, depth, mat):
    for i in range(total_shelves):
        z_position = i * spacing
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
        shelf = bpy.context.object
        shelf.scale = (width / 2, depth / 2, height / 2)
        shelf.name = f"Shelf_{i + 1}"
        shelf.data.materials.append(mat)

generate_shelves(number_of_shelves, spacing_between_shelves, shelf_width, shelf_height, shelf_depth, wooden_material)

thickness_of_panels = 0.05
height_of_panels = number_of_shelves * spacing_between_shelves

for i in range(2):
    x_position = (shelf_width / 2) * (i * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, height_of_panels / 2))
    side_panel = bpy.context.object
    side_panel.scale = (thickness_of_panels / 2, shelf_depth / 2, height_of_panels / 2)
    side_panel.name = f"Panel_{i + 1}"
    side_panel.data.materials.append(wooden_material)


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
