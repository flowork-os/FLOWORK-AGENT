# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_creating_cat_bed" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for creating cat bed.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_light_gray = bpy.data.materials.new(name='Material Light Gray')
material_light_gray.diffuse_color = (0.8, 0.8, 0.8, 1)
material_dark_brown = bpy.data.materials.new(name='Material Dark Brown')
material_dark_brown.diffuse_color = (0.4, 0.2, 0.1, 1)

bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.2, location=(0, 0, 0))
base_cylinder = bpy.context.object
base_cylinder.name = 'Base'
base_cylinder.data.materials.append(material_light_gray)

bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=0.2, location=(0, 0, 0.2))
sides_torus = bpy.context.object
sides_torus.name = 'Sides'
sides_torus.data.materials.append(material_dark_brown)

bpy.ops.mesh.primitive_cylinder_add(radius=0.9, depth=0.15, location=(0, 0, 0.025))
soft_interior_cylinder = bpy.context.object
soft_interior_cylinder.name = 'Soft Interior'
soft_interior_cylinder.data.materials.append(material_light_gray)


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
