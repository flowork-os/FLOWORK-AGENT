# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_code_to_create_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender code to create bookshelf

import bpy

# Start by clearing the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood-like material
material_wood = bpy.data.materials.new(name="MaterialWood")
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)

# Shelf configuration
shelf_dimensions = {'height': 0.1, 'depth': 0.4, 'width': 0.8}
spacing_between_shelves = 0.6
shelf_quantity = 5

# Function to generate shelves

def add_shelf(index):
    z_position = index * spacing_between_shelves
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    new_shelf = bpy.context.object
    new_shelf.scale = (shelf_dimensions['width'] / 2, shelf_dimensions['depth'] / 2, shelf_dimensions['height'] / 2)
    new_shelf.name = f"Shelf {index + 1}"
    new_shelf.data.materials.append(material_wood)

# Adding shelves to the scene
for i in range(shelf_quantity):
    add_shelf(i)

# Panel specifications
panel_specs = {'thickness': 0.05, 'height': shelf_quantity * spacing_between_shelves, 'depth': shelf_dimensions['depth']}

# Function to create side panels

def add_panel(index):
    x_position = (shelf_dimensions['width'] / 2) * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, panel_specs['height'] / 2))
    new_panel = bpy.context.object
    new_panel.scale = (panel_specs['thickness'] / 2, panel_specs['depth'] / 2, panel_specs['height'] / 2)
    new_panel.name = f"Side Panel {index + 1}"
    new_panel.data.materials.append(material_wood)

# Creating both side panels
for i in range(2):
    add_panel(i)


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
