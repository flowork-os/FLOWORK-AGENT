# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_bookshelf_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of bookshelf in a Blender script

import bpy

# Remove all mesh objects in the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the wood texture
wood_texture = bpy.data.materials.new(name='WoodTexture')
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)

# Parameters for the shelf dimensions
shelves_count = 5
shelf_params = {'width': 2, 'height': 0.1, 'depth': 0.4, 'spacing': 0.6}

# Create shelves using a loop
for index in range(shelves_count):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * shelf_params['spacing']))
    shelf = bpy.context.object
    shelf.scale = (shelf_params['width'] / 2, shelf_params['depth'] / 2, shelf_params['height'] / 2)
    shelf.name = f'Shelf_{index + 1}'
    shelf.data.materials.append(wood_texture)

# Create vertical supports
for index in range(2):
    x_coord = shelf_params['width'] / 2 * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_coord, 0, shelves_count * shelf_params['spacing'] / 2))
    support = bpy.context.object
    support.scale = (0.025, 0.025, shelves_count * shelf_params['spacing'] / 2)
    support.name = f'Support_{index + 1}'
    support.data.materials.append(wood_texture)


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
