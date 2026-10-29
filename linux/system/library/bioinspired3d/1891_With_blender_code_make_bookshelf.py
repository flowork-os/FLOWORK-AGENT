# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_code_make_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender code make bookshelf

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material setup for the shelves
wooden_texture = bpy.data.materials.new(name="WoodTexture")
wooden_texture.diffuse_color = (0.55, 0.27, 0.07, 1)

# Parameters for shelf creation
shelf_params = {
    'width': 2,
    'height': 0.1,
    'depth': 0.4,
    'spacing': 0.6,
    'count': 5
}

# Function to add a shelf
def add_shelf(index):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * shelf_params['spacing']))
    shelf = bpy.context.object
    shelf.scale = (shelf_params['width'] / 2, shelf_params['depth'] / 2, shelf_params['height'] / 2)
    shelf.name = f"Shelf_{index + 1}"
    shelf.data.materials.append(wooden_texture)

# Create all shelves
for i in range(shelf_params['count']):
    add_shelf(i)

# Parameters for the sides
side_dimensions = {
    'thickness': 0.05,
    'total_height': shelf_params['count'] * shelf_params['spacing']
}

# Function to add a side
def add_side(index):
    x_position = (shelf_params['width'] / 2) * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, side_dimensions['total_height'] / 2))
    side = bpy.context.object
    side.scale = (side_dimensions['thickness'] / 2, shelf_params['depth'] / 2, side_dimensions['total_height'] / 2)
    side.name = f"Side_{index + 1}"
    side.data.materials.append(wooden_texture)

# Create both sides
for i in range(2):
    add_side(i)


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
