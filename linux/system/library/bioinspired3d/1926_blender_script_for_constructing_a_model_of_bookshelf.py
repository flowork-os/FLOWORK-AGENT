# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_constructing_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for constructing a model of bookshelf

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material resembling wood
wood_texture = bpy.data.materials.new(name="Wood Texture")
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)

# Parameters for the shelf configuration
shelf_params = {
    'width': 2,
    'height': 0.1,
    'depth': 0.4,
    'spacing': 0.5,
    'count': 5
}

# Function to add a shelf
def add_shelf(index):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * shelf_params['spacing']))
    shelf_object = bpy.context.object
    shelf_object.scale = (shelf_params['width'] / 2, shelf_params['depth'] / 2, shelf_params['height'] / 2)
    shelf_object.name = f"Shelf {index + 1}"
    shelf_object.data.materials.append(wood_texture)

# Create shelves using the defined parameters
for i in range(shelf_params['count']):
    add_shelf(i)

# Create the side panels
panel_thickness = 0.05
panel_height = shelf_params['count'] * shelf_params['spacing']

for side in range(2):
    x_offset = (shelf_params['width'] / 2) * (side * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_offset, 0, panel_height / 2))
    side_panel = bpy.context.object
    side_panel.scale = (panel_thickness / 2, shelf_params['depth'] / 2, panel_height / 2)
    side_panel.name = f"Side Panel {side + 1}"
    side_panel.data.materials.append(wood_texture)


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
