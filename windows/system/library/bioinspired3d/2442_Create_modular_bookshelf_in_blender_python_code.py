# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_modular_bookshelf_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create modular bookshelf in blender python code

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material = bpy.data.materials.new(name='WoodFinish')
material.diffuse_color = (0.4, 0.2, 0.05, 1)

def construct_cube_with_base(coords):
    bpy.ops.mesh.primitive_cube_add(size=1, location=coords)
    cube_instance = bpy.context.object
    cube_instance.name = 'Cube Shelf'
    cube_instance.data.materials.append(material)
    
    base_coords = (coords[0], coords[1], coords[2] - 0.55)
    bpy.ops.mesh.primitive_cube_add(size=1.1, scale=(1, 1, 0.1), location=base_coords)
    base_instance = bpy.context.object
    base_instance.name = 'Shelf Base'
    base_instance.data.materials.append(material)

for x in range(2):
    for y in range(2):
        construct_cube_with_base((x * 1.2, y * 1.2, 0.5))


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
