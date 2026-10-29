# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_code_that_makes_modular_shelving_unit" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender code that makes modular shelving unit.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create material for the shelves
material_gray = bpy.data.materials.new(name='ShelfMaterial')
material_gray.diffuse_color = (0.8, 0.8, 0.8, 1)

# Shelf dimensions
width, height, depth = 2, 0.1, 0.5

# Create shelves using a loop
for i in range(4):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, i))
    shelf_object = bpy.context.object
    shelf_object.scale = (width, depth, height)
    shelf_object.name = f'Shelf_{i + 1}'
    shelf_object.data.materials.append(material_gray)

# Dimensions for side supports
support_width, support_height, support_depth = 0.1, 4, 0.5

# Create side supports
for j in range(2):
    x_position = width * (j * 2 - 1) / 2
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_position, 0, support_height / 2 - 0.5))
    support_object = bpy.context.object
    support_object.scale = (support_width, support_depth, support_height)
    support_object.name = f'Support_{j + 1}'
    support_object.data.materials.append(material_gray)


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
