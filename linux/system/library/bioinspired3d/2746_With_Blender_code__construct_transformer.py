# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_Blender_code__construct_transformer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With Blender code, construct transformer

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

mat_body = bpy.data.materials.new(name="Body")
mat_body.diffuse_color = (0.5, 0.5, 0.5, 1)
mat_coil = bpy.data.materials.new(name="Coil")
mat_coil.diffuse_color = (0.1, 0.1, 0.1, 1)

bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))
main_body = bpy.context.object
main_body.name = "Cylinder Body"
main_body.data.materials.append(mat_body)

for i in range(3):
    z_position = -0.5 + i * 0.6
    bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=0.1, location=(0, 0, z_position))
    coil_part = bpy.context.object
    coil_part.name = f"Spiral_{i + 1}"
    coil_part.data.materials.append(mat_coil)


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
