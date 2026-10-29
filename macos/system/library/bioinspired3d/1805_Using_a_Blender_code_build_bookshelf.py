# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_a_Blender_code_build_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using a Blender code build bookshelf

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define material for the shelves
wood_texture = bpy.data.materials.new(name='WoodTexture')
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)  # Represents wood color

# Set shelf parameters
shelves = 5
shelf_dims = (2, 0.1, 0.4)
spacing_between_shelves = 0.5

def add_shelf(index):
    z_position = index * spacing_between_shelves
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    new_shelf = bpy.context.object
    new_shelf.scale = (shelf_dims[0] / 2, shelf_dims[2] / 2, shelf_dims[1] / 2)
    new_shelf.name = f'Shelf_{index + 1}'
    new_shelf.data.materials.append(wood_texture)

# Generate shelves
for i in range(shelves):
    add_shelf(i)

# Define side panel dimensions
side_panel_thickness = 0.05
side_panel_height = shelves * spacing_between_shelves

# Function to create side panels
def add_side_panel(position):
    x_position = shelf_dims[0] / 2 * (position * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, side_panel_height / 2))
    side_panel = bpy.context.object
    side_panel.scale = (side_panel_thickness / 2, shelf_dims[2] / 2, side_panel_height / 2)
    side_panel.name = f'SidePanel_{position + 1}'
    side_panel.data.materials.append(wood_texture)

# Create side panels
for pos in range(2):
    add_side_panel(pos)


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
