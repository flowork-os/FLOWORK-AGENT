# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_python_code__make_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender python code, make sofa

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the sofa
sofa_material = bpy.data.materials.new(name="Sofa Material")
sofa_material.diffuse_color = (0.6, 0.6, 0.6, 1)  # Light gray color

# Function to create a cube with specific parameters

def create_cube(size, location, scale, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(material)
    return cube

# Create the main components of the sofa
base = create_cube(2, (0, 0, 0.5), (2, 1, 0.3), "Base", sofa_material)
backrest = create_cube(2, (0, -0.9, 1.15), (2, 0.2, 0.7), "Backrest", sofa_material)

# Create armrests
for index in range(2):
    position_x = 1.9 * (index * 2 - 1)
    create_cube(2, (position_x, 0, 0.85), (0.2, 1, 0.5), f"Armrest {index + 1}", sofa_material)


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
