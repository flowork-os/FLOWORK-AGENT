# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_python_blender_code_generate_a_model_of_puzzle_cube" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using python blender code generate a model of puzzle cube.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

color_definitions = {
    "white": (1, 1, 1, 1),
    "yellow": (1, 1, 0, 1),
    "red": (1, 0, 0, 1),
    "orange": (1, 0.5, 0, 1),
    "blue": (0, 0, 1, 1),
    "green": (0, 1, 0, 1)
}

def generate_materials():
    materials = []
    for color_name, color_value in color_definitions.items():
        mat = bpy.data.materials.new(name=color_name)
        mat.diffuse_color = color_value
        materials.append(mat)
    return materials

material_collection = generate_materials()

cube_scale = 0.95
offset = 0.05

for i in range(3):
    for j in range(3):
        for k in range(3):
            bpy.ops.mesh.primitive_cube_add(size=cube_scale, location=(i * (cube_scale + offset), j * (cube_scale + offset), k * (cube_scale + offset)))
            cube_object = bpy.context.object
            cube_object.name = f"Cube_{i}_{j}_{k}"
            for idx in range(6):
                cube_object.data.polygons[idx].material_index = idx % len(material_collection)
                cube_object.data.materials.append(material_collection[idx % len(material_collection)])


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
