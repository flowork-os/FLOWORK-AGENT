# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_for_constructing_a_model_of_cupcake" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script for constructing a model of cupcake

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

cupcake_material = bpy.data.materials.new(name='Cupcake Material')
cupcake_material.diffuse_color = (0.85, 0.38, 0.12, 1)
frosting_material = bpy.data.materials.new(name='Frosting Material')
frosting_material.diffuse_color = (1.0, 0.9, 0.8, 1)

bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1, location=(0, 0, 0.5))
cupcake_base = bpy.context.object
cupcake_base.name = 'Cupcake Base'
cupcake_base.data.materials.append(cupcake_material)

for i, (major_radius, minor_radius, z_location) in enumerate([(1, 0.3, 1.1), (0.8, 0.25, 1.4), (0.6, 0.2, 1.6)]):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_radius, minor_radius=minor_radius, location=(0, 0, z_location))
    frosting = bpy.context.object
    frosting.name = f'Frosting Layer {i + 1}'
    frosting.data.materials.append(frosting_material)

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, 0, 1.9))
frosting_top = bpy.context.object
frosting_top.name = 'Frosting Top'
frosting_top.data.materials.append(frosting_material)


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
