# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_chocolate_bar_using_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct chocolate bar using Blender code

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

mat_chocolate = bpy.data.materials.new(name='Chocolate Material')
mat_chocolate.diffuse_color = (0.24, 0.15, 0.10, 1)

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
chocolate_block = bpy.context.object
chocolate_block.name = 'Chocolate Block'
chocolate_block.scale = (1, 0.5, 0.1)
chocolate_block.data.materials.append(mat_chocolate)

segments_x = 8
segments_y = 4
segment_width = 0.2
segment_gap = 0.05

def add_segment(i, j):
    x_pos = (i - segments_x / 2 + 0.5) * (segment_width + segment_gap)
    y_pos = (j - segments_y / 2 + 0.5) * (segment_width + segment_gap)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_pos, y_pos, 0.1))
    new_segment = bpy.context.object
    new_segment.name = f'Segment {i * segments_y + j + 1}'
    new_segment.scale = (segment_width, segment_width, 0.1)
    new_segment.data.materials.append(mat_chocolate)

for i in range(segments_x):
    for j in range(segments_y):
        add_segment(i, j)


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
