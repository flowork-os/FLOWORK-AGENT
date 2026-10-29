# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_to_construct_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script to construct bookshelf.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the shelves
material_wood = bpy.data.materials.new(name='WoodTexture')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)  # Color similar to wood

# Shelf configuration
shelf_dim = (2, 0.1, 0.4)
spacing = 0.5
shelves_count = 5

# Generate shelves
for index in range(shelves_count):
    z_offset = index * spacing
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_offset))
    shelf_cube = bpy.context.object
    shelf_cube.scale = (shelf_dim[0] / 2, shelf_dim[2] / 2, shelf_dim[1] / 2)
    shelf_cube.name = f'Shelf_{index + 1}'
    shelf_cube.data.materials.append(material_wood)

# Side panel parameters
panel_size = (0.05, shelves_count * spacing)

# Create side panels
for index in range(2):
    x_pos = (shelf_dim[0] / 2) * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_pos, 0, panel_size[1] / 2))
    side_cube = bpy.context.object
    side_cube.scale = (panel_size[0] / 2, shelf_dim[2] / 2, panel_size[1] / 2)
    side_cube.name = f'SidePanel_{index + 1}'
    side_cube.data.materials.append(material_wood)


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
