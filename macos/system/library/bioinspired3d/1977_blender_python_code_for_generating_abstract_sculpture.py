# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_generating_abstract_sculpture" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for generating abstract sculpture

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

sculpture_color = bpy.data.materials.new(name="Sculpture Material")
sculpture_color.diffuse_color = (0.6, 0.6, 0.6, 1)  # Light gray color

bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.2, location=(0, 0, 0.1))
base_object = bpy.context.object
base_object.name = "Base"
base_object.data.materials.append(sculpture_color)

locations = [(0, 0, z) for z in range(1, 5)]
major_radii = [0.5, 0.4, 0.3, 0.2]
rotations = [(0, 0, math.pi/4), (0, math.pi/4, 0), (math.pi/4, 0, 0), (0, 0, 0)]

for loc, radius, rot in zip(locations, major_radii, rotations):
    bpy.ops.mesh.primitive_torus_add(align='WORLD', location=loc, major_radius=radius, minor_radius=0.1, rotation=rot)
    torus = bpy.context.object
    torus.name = f"Shape {locations.index(loc)+1}"
    torus.data.materials.append(sculpture_color)

for i in range(1, 4):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(0, 0, 1.5 + i))
    rod = bpy.context.object
    rod.name = f"Rod {i}"
    rod.data.materials.append(sculpture_color)


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
