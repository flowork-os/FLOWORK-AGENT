# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_logo_in_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create logo in code in Blender

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

logo_material = bpy.data.materials.new(name='LogoMaterial')
logo_material.diffuse_color = (0.8, 0.2, 0.2, 1)  # RGB for red

bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.1, location=(0, 0, 0))
base_cylinder = bpy.context.object
base_cylinder.name = 'BaseCylinder'
base_cylinder.data.materials.append(logo_material)

bpy.ops.mesh.primitive_cube_add(size=0.6, location=(0, 0, 0.05))
horizontal_cross = bpy.context.object
horizontal_cross.scale = (1, 0.1, 0.1)
horizontal_cross.name = 'HorizontalCross'
horizontal_cross.data.materials.append(logo_material)

bpy.ops.mesh.primitive_cube_add(size=0.6, location=(0, 0, 0.05))
vertical_cross = bpy.context.object
vertical_cross.scale = (0.1, 1, 0.1)
vertical_cross.name = 'VerticalCross'
vertical_cross.data.materials.append(logo_material)


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
