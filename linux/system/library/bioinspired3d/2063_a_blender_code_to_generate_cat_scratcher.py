# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_to_generate_cat_scratcher" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code to generate cat scratcher.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

rough_texture_material = bpy.data.materials.new(name="Rough Texture")
rough_texture_material.diffuse_color = (0.5, 0.3, 0.2, 1)

def create_structure(shape, params, name, material):
    if shape == 'cube':
        bpy.ops.mesh.primitive_cube_add(size=params[0], location=params[1])
    elif shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(radius=params[0], depth=params[1], location=params[2])
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)

create_structure('cube', (2, (0, 0, -0.5)), "Base", rough_texture_material)
create_structure('cylinder', (0.3, 3, (0, 0, 1)), "Scratching Post", rough_texture_material)
create_structure('cylinder', (0.32, 2.8, (0, 0, 1)), "Worn Scratching Surface", rough_texture_material)
create_structure('cube', (1, (0, 0, 2.5)), "Top Platform", rough_texture_material)


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
