# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_Blender_Python_script_that_makes_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write Blender Python script that makes a model of bookshelf.

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the shelves
material_wood = bpy.data.materials.new(name='ShelfMaterial')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)  # Wood-like color

# Define shelf dimensions and number of shelves
shelf_dims = {'width': 2, 'height': 0.1, 'depth': 0.4, 'spacing': 0.6}
num_of_shelves = 5

# Create shelves using a loop
for i in range(num_of_shelves):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, i * shelf_dims['spacing']))
    shelf = bpy.context.object
    shelf.scale = (shelf_dims['width'] / 2, shelf_dims['depth'] / 2, shelf_dims['height'] / 2)
    shelf.name = f'Shelf_{i + 1}'
    shelf.data.materials.append(material_wood)

# Create side panels
panel_thickness = 0.05
panel_height = num_of_shelves * shelf_dims['spacing']

for i in range(2):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(shelf_dims['width'] / 2 * (i * 2 - 1), 0, panel_height / 2))
    panel = bpy.context.object
    panel.scale = (panel_thickness / 2, shelf_dims['depth'] / 2, panel_height / 2)
    panel.name = f'SidePanel_{i + 1}'
    panel.data.materials.append(material_wood)


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
