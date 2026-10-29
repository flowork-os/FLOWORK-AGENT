# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_sofa_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate sofa using code in Blender

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

sofa_material = bpy.data.materials.new(name='SofaMaterial')
sofa_material.diffuse_color = (0.5, 0.25, 0.1, 1)  # A warm brown hue

def add_cube(size, location, name, scale):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.scale = scale
    cube.name = name
    cube.data.materials.append(sofa_material)

add_cube(2, (0, 0, 0.5), 'SofaBase', (2, 1, 0.2))
add_cube(2, (0, -1, 1.1), 'SofaBackrest', (2, 0.2, 0.6))

for index in range(2):
    position_x = 1.8 * (index * 2 - 1)
    add_cube(2, (position_x, 0, 0.8), f'SofaArmrest{index + 1}', (0.2, 1, 0.4))

for index in range(3):
    position_x = (index - 1) * 1.2
    add_cube(2, (position_x, 0, 0.7), f'SofaCushion{index + 1}', (0.4, 1, 0.2))


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
