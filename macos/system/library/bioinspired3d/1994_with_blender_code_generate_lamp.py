# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_code_generate_lamp" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender code generate lamp

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_light = bpy.data.materials.new(name='MaterialLight')
material_light.diffuse_color = (0.8, 0.8, 0.8, 1)

material_decor = bpy.data.materials.new(name='MaterialDecor')
material_decor.diffuse_color = (0.5, 0.2, 0.2, 1)

bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.1, location=(0, 0, 0))
base_lamp = bpy.context.object
base_lamp.name = 'Base'
base_lamp.data.materials.append(material_light)

bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1, location=(0, 0, 0.55))
stand_lamp = bpy.context.object
stand_lamp.name = 'Stand'
stand_lamp.data.materials.append(material_light)

bpy.ops.mesh.primitive_cone_add(radius1=0.6, radius2=0.2, depth=0.8, location=(0, 0, 1.3))
shade_lamp = bpy.context.object
shade_lamp.name = 'Shade'
shade_lamp.data.materials.append(material_light)

bpy.ops.mesh.primitive_torus_add(major_radius=0.6, minor_radius=0.05, location=(0, 0, 0.05))
decorative_torus = bpy.context.object
decorative_torus.name = 'Decor'
decorative_torus.data.materials.append(material_decor)


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
