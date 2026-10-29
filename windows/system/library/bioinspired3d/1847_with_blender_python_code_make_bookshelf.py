# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_python_code_make_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender python code make bookshelf

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define material for the structure
wooden_texture = bpy.data.materials.new(name='WoodTexture')
wooden_texture.diffuse_color = (0.55, 0.27, 0.07, 1)  # Wood-like color

# Class for building the shelf unit
class ShelfUnit:
    def __init__(self, height, depth, width, spacing, shelf_count):
        self.height = height
        self.depth = depth
        self.width = width
        self.spacing = spacing
        self.shelf_count = shelf_count

    def add_shelves(self):
        for index in range(self.shelf_count):
            self.create_shelf(index)

    def create_shelf(self, index):
        z_position = index * self.spacing
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
        shelf = bpy.context.object
        shelf.scale = (self.width / 2, self.depth / 2, self.height / 2)
        shelf.name = f'Shelf_{index + 1}'
        shelf.data.materials.append(wooden_texture)

# Parameters for the shelf unit
shelf_height = 0.1
shelf_depth = 0.3
shelf_width = 0.5
shelf_spacing = 0.4
number_of_shelves = 4

# Create and add shelves
shelf_unit = ShelfUnit(shelf_height, shelf_depth, shelf_width, shelf_spacing, number_of_shelves)
shelf_unit.add_shelves()

# Create side panels
panel_thickness = 0.05
panel_height = number_of_shelves * shelf_spacing

for i in range(2):
    x_position = (shelf_width / 2) * (i * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, panel_height / 2))
    side_panel = bpy.context.object
    side_panel.scale = (panel_thickness / 2, shelf_depth / 2, panel_height / 2)
    side_panel.name = f'SidePanel_{i + 1}'
    side_panel.data.materials.append(wooden_texture)


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
