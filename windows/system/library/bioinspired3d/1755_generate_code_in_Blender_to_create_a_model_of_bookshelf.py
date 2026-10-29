# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_code_in_Blender_to_create_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate code in Blender to create a model of bookshelf.

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize the bookshelf material
bookshelf_material = bpy.data.materials.new(name='BookshelfWood')
bookshelf_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Create the bookshelf using an object-oriented approach
class Bookshelf:
    def __init__(self):
        self.create_side_panel((-1, 0, 1), 'Left Side')
        self.create_side_panel((1, 0, 1), 'Right Side')
        self.create_shelves()

    def create_side_panel(self, location, name):
        bpy.ops.mesh.primitive_cube_add(size=2, location=location)
        side_panel = bpy.context.object
        side_panel.scale = (0.1, 1, 2)
        side_panel.name = name
        side_panel.data.materials.append(bookshelf_material)

    def create_shelves(self):
        for i in range(3):
            z_position = 0.5 + i * 1.0
            bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
            shelf = bpy.context.object
            shelf.scale = (1, 1, 0.1)
            shelf.name = f'Shelf {i + 1}'
            shelf.data.materials.append(bookshelf_material)

# Instantiate the bookshelf
Bookshelf()


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
