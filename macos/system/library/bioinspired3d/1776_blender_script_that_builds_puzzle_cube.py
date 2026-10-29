# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_builds_puzzle_cube" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that builds puzzle cube.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def add_cube_at(position, color_name, color_rgba):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    cube = bpy.context.object
    cube.name = color_name
    material = bpy.data.materials.new(name=color_name)
    material.diffuse_color = color_rgba
    cube.data.materials.append(material)

color_palette = [
    ('Ruby', (1, 0, 0, 1)),
    ('Verdant', (0, 1, 0, 1)),
    ('Cobalt', (0, 0, 1, 1)),
    ('Amber', (1, 1, 0, 1)),
    ('Cerulean', (0, 1, 1, 1)),
    ('Magenta', (1, 0, 1, 1)),
    ('Coral', (1, 0.5, 0, 1)),
    ('Lilac', (0.5, 0, 0.5, 1)),
]

cube_positions = [
    (0, 0, 0),
    (1, 0, 0),
    (0, 1, 0),
    (0, 0, 1),
    (1, 1, 0),
    (1, 0, 1),
    (0, 1, 1),
    (1, 1, 1)
]

for index in range(len(cube_positions)):
    add_cube_at(cube_positions[index], color_palette[index][0], color_palette[index][1])


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
