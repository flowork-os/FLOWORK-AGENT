# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_bookshelf_in_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct bookshelf in Blender code

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood material
material_wood = bpy.data.materials.new(name='Wooden Finish')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)

# Define parameters for shelves and panels
shelf_params = {'width': 3.0, 'height': 0.1, 'depth': 0.5, 'spacing': 1.2}
num_shelves = 5

# Function to add shelves

def add_shelf(index):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * shelf_params['spacing']))
    shelf_object = bpy.context.object
    shelf_object.scale = (shelf_params['width'] / 2, shelf_params['depth'] / 2, shelf_params['height'] / 2)
    shelf_object.name = f'Shelf_{index + 1}'
    shelf_object.data.materials.append(material_wood)

# Create shelves
for i in range(num_shelves):
    add_shelf(i)

# Create the side panels
panel_thickness = 0.05
panel_height = (num_shelves - 1) * shelf_params['spacing'] + shelf_params['height']

for i in range(2):
    x_coord = (shelf_params['width'] / 2) * (i * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_coord, 0, panel_height / 2))
    side_panel_object = bpy.context.object
    side_panel_object.scale = (panel_thickness / 2, shelf_params['depth'] / 2, panel_height / 2)
    side_panel_object.name = f'Side_Panel_{i + 1}'
    side_panel_object.data.materials.append(material_wood)


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
