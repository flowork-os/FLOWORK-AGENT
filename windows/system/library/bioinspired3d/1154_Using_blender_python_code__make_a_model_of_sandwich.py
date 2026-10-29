# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_python_code__make_a_model_of_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender python code, make a model of sandwich

import bpy

# Remove all mesh objects from the current Blender scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define sandwich materials
bread_mat = bpy.data.materials.new(name='Bread')
bread_mat.diffuse_color = (0.97, 0.88, 0.72, 1)
lettuce_mat = bpy.data.materials.new(name='Lettuce')
lettuce_mat.diffuse_color = (0.12, 0.54, 0.12, 1)
tomato_mat = bpy.data.materials.new(name='Tomato')
tomato_mat.diffuse_color = (0.88, 0.14, 0.08, 1)
cheese_mat = bpy.data.materials.new(name='Cheese')
cheese_mat.diffuse_color = (1.0, 0.82, 0.01, 1)

# Create sandwich components using a loop
components = [
    ('Bottom Bread', (0, 0, 0), 0.1, bread_mat),
    ('Lettuce', (0, 0, 0.2), 0.05, lettuce_mat),
    ('Tomato', (0, 0, 0.3), 0.05, tomato_mat),
    ('Cheese', (0, 0, 0.4), 0.05, cheese_mat),
    ('Top Bread', (0, 0, 0.6), 0.1, bread_mat)
]

for name, loc, scale, mat in components:
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale[2] = scale
    obj.data.materials.append(mat)


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
