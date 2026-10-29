# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_generates_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that generates bookshelf.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the shelves
wood_material = bpy.data.materials.new(name="WoodMaterial")
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Brown wood color

# Function to create a shelf
def create_shelf(index):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * 0.6))
    shelf = bpy.context.object
    shelf.scale = (1, 0.2, 0.05)
    shelf.name = f"Shelf_{index + 1}"
    shelf.data.materials.append(wood_material)

# Create multiple shelves
for j in range(5):
    create_shelf(j)

# Function to create side panels
def create_side_panel(index):
    x_position = (1 * (index * 2 - 1))
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, 1.5))
    side_panel = bpy.context.object
    side_panel.scale = (0.025, 0.2, 1.5)
    side_panel.name = f"SidePanel_{index + 1}"
    side_panel.data.materials.append(wood_material)

# Create side panels
for k in range(2):
    create_side_panel(k)


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
