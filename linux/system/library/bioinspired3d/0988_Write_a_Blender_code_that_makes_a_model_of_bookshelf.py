# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_Blender_code_that_makes_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a Blender code that makes a model of bookshelf

import bpy

# Step 1: Clear the current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the shelf
shelf_color = bpy.data.materials.new(name='WoodShelf')
shelf_color.diffuse_color = (0.55, 0.27, 0.07, 1)  # Color for wood texture

# Step 2: Function to add a shelf
def add_shelf(index):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * 0.6))
    shelf = bpy.context.object
    shelf.scale = (1, 0.2, 0.05)
    shelf.name = f'Shelf_{index + 1}'
    shelf.data.materials.append(shelf_color)

for i in range(5):
    add_shelf(i)

# Step 3: Function to create side panels
def add_side_panel(index):
    bpy.ops.mesh.primitive_cube_add(size=2, location=((1 if index == 1 else -1) * 1, 0, 1.5))
    panel = bpy.context.object
    panel.scale = (0.025, 0.2, 1.5)
    panel.name = f'SidePanel_{index + 1}'
    panel.data.materials.append(shelf_color)

for i in range(2):
    add_side_panel(i)


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
