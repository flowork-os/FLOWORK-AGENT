# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_python_code_build_chocolate_bar" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender python code build chocolate bar

import bpy

def clear_scene():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

clear_scene()

choco_material = bpy.data.materials.new(name='Chocolate Color')
choco_material.diffuse_color = (0.24, 0.15, 0.10, 1)

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
bar_base = bpy.context.object
bar_base.name = 'Base Chocolate'
bar_base.scale = (1, 0.5, 0.1)
bar_base.data.materials.append(choco_material)

num_x_segments = 8
num_y_segments = 4
segment_dim = 0.2
spacing = 0.05

for x in range(num_x_segments):
    for y in range(num_y_segments):
        x_coord = (x - num_x_segments / 2 + 0.5) * (segment_dim + spacing)
        y_coord = (y - num_y_segments / 2 + 0.5) * (segment_dim + spacing)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x_coord, y_coord, 0.1))
        segment_piece = bpy.context.object
        segment_piece.name = f'Segment {x * num_y_segments + y + 1}'
        segment_piece.scale = (segment_dim, segment_dim, 0.1)
        segment_piece.data.materials.append(choco_material)


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
