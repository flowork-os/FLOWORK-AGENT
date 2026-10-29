# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_horse_brush_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of horse brush in a Blender script

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

brush_material = bpy.data.materials.new(name='BrushMaterial')
brush_material.diffuse_color = (0.55, 0.27, 0.07, 1)
bristle_material = bpy.data.materials.new(name='BristleMaterial')
bristle_material.diffuse_color = (0.33, 0.33, 0.33, 1)

bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.2, location=(0, 0, 0))
base = bpy.context.object
base.name = 'BrushBase'
base.data.materials.append(brush_material)

bpy.ops.mesh.primitive_cylinder_add(radius=0.9, depth=0.3, location=(0, 0, 0.25))
bristles = bpy.context.object
bristles.name = 'Bristles'
bristles.data.materials.append(bristle_material)

bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0, 0, 0.2))
strap = bpy.context.object
strap.name = 'Strap'
strap.scale = (2, 0.1, 0.1)
strap.data.materials.append(brush_material)

strap.location.z = 0.2


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
