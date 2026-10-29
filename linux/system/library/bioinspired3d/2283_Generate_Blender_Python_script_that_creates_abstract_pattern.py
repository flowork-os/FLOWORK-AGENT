# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_Python_script_that_creates_abstract_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender Python script that creates abstract pattern.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_gray = bpy.data.materials.new(name='Gray Material')
material_gray.diffuse_color = (0.5, 0.5, 0.5, 1)

def create_shapes():
    for index in range(5):
        theta = index * math.pi / 5
        
        bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.1, location=(math.cos(theta), math.sin(theta), 0))
        torus_object = bpy.context.object
        torus_object.name = f'Torus_{index + 1}'
        torus_object.data.materials.append(material_gray)

        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2, location=(math.cos(theta), math.sin(theta), 0), rotation=(0, 0, theta))
        cylinder_object = bpy.context.object
        cylinder_object.name = f'Cylinder_{index + 1}'
        cylinder_object.data.materials.append(material_gray)

        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(math.cos(theta), math.sin(theta), 0))
        sphere_object = bpy.context.object
        sphere_object.name = f'Sphere_{index + 1}'
        sphere_object.data.materials.append(material_gray)

create_shapes()


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
