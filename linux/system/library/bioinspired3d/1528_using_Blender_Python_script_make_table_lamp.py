# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_Python_script_make_table_lamp" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender Python script make table lamp.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

base_color_material = bpy.data.materials.new(name='Base Color Material')
base_color_material.diffuse_color = (0.2, 0.2, 0.2, 1)
shade_color_material = bpy.data.materials.new(name='Shade Color Material')
shade_color_material.diffuse_color = (1, 1, 1, 0.8)

def setup_lamp():
    bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.1, location=(0, 0, 0))
    base = bpy.context.object
    base.name = 'Lamp Base'
    base.data.materials.append(base_color_material)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(0, 0, 0.55))
    pole = bpy.context.object
    pole.name = 'Lamp Pole'
    pole.data.materials.append(base_color_material)

    bpy.ops.mesh.primitive_cone_add(radius1=0.6, radius2=0.2, depth=0.8, location=(0, 0, 1.4))
    shade = bpy.context.object
    shade.name = 'Lamp Shade'
    shade.data.materials.append(shade_color_material)

setup_lamp()


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
