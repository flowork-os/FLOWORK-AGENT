# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_blender_code_generate_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a blender code generate bookshelf

import bpy

# Clear the scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the shelves
shelf_material = bpy.data.materials.new(name='ShelfMaterial')
shelf_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Shelf configuration
shelf_dims = {'width': 2.0, 'height': 0.1, 'depth': 0.4}
number_of_shelves = 5
spacing = 0.6

# Create shelves using a class-based approach
class Shelf:
    def __init__(self, index):
        self.index = index
        self.create_shelf()

    def create_shelf(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, self.index * spacing))
        shelf_obj = bpy.context.object
        shelf_obj.scale = (shelf_dims['width'] / 2, shelf_dims['depth'] / 2, shelf_dims['height'] / 2)
        shelf_obj.name = f'Shelf_{self.index + 1}'
        shelf_obj.data.materials.append(shelf_material)

for i in range(number_of_shelves):
    Shelf(i)

# Create side panels using a similar class-based approach
class SidePanel:
    def __init__(self, index):
        self.index = index
        self.create_panel()

    def create_panel(self):
        panel_width = 0.05
        panel_height = number_of_shelves * spacing
        x_position = (shelf_dims['width'] / 2) * (self.index * 2 - 1)
        bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, panel_height / 2))
        panel_obj = bpy.context.object
        panel_obj.scale = (panel_width / 2, shelf_dims['depth'] / 2, panel_height / 2)
        panel_obj.name = f'Panel_{self.index + 1}'
        panel_obj.data.materials.append(shelf_material)

for i in range(2):
    SidePanel(i)


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
