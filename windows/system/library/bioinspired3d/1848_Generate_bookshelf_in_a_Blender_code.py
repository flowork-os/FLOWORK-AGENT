# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_bookshelf_in_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate bookshelf in a Blender code

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_wood = bpy.data.materials.new(name='MaterialWood')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)  # Represents wood color

def add_single_shelf(index, height, depth, width, spacing):
    z_position = index * spacing
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    shelf = bpy.context.object
    shelf.scale = (width / 2, depth / 2, height / 2)
    shelf.name = f'Shelf_{index + 1}'
    shelf.data.materials.append(material_wood)

shelf_height = 0.1
shelf_depth = 0.3
shelf_width = 0.5
shelf_spacing = 0.4
total_shelves = 4

for i in range(total_shelves):
    add_single_shelf(i, shelf_height, shelf_depth, shelf_width, shelf_spacing)

thickness_of_panels = 0.05
height_of_panels = total_shelves * shelf_spacing

for i in range(2):
    x_position = (shelf_width / 2) * (i * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, height_of_panels / 2))
    side_panel = bpy.context.object
    side_panel.scale = (thickness_of_panels / 2, shelf_depth / 2, height_of_panels / 2)
    side_panel.name = f'SidePanel_{i + 1}'
    side_panel.data.materials.append(material_wood)


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
