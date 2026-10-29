# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_creating_a_model_of_table_lamp" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for creating a model of table lamp.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for lamp parts
material_for_base = bpy.data.materials.new(name='Material for Base')
material_for_base.diffuse_color = (0.2, 0.2, 0.2, 1)
material_for_shade = bpy.data.materials.new(name='Material for Shade')
material_for_shade.diffuse_color = (1, 1, 1, 0.8)

# Create base
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.1, location=(0, 0, 0))
base_object = bpy.context.object
base_object.name = 'Base'
base_object.data.materials.append(material_for_base)

# Create pole
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(0, 0, 0.55))
pole_object = bpy.context.object
pole_object.name = 'Pole'
pole_object.data.materials.append(material_for_base)

# Create shade
bpy.ops.mesh.primitive_cone_add(radius1=0.6, radius2=0.2, depth=0.8, location=(0, 0, 1.4))
shade_object = bpy.context.object
shade_object.name = 'Shade'
shade_object.data.materials.append(material_for_shade)


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
