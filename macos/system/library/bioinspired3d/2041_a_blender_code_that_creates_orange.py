# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_creates_orange" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that creates orange.

import bpy

# Clear the current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the objects
material_fruit = bpy.data.materials.new(name='MaterialFruit')
material_fruit.diffuse_color = (1.0, 0.55, 0.0, 1)

material_stem = bpy.data.materials.new(name='MaterialStem')
material_stem.diffuse_color = (0.33, 0.42, 0.18, 1)

# Create the fruit object
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, location=(0, 0, 0))
fruit_object = bpy.context.object
fruit_object.name = 'FruitObject'
fruit_object.data.materials.append(material_fruit)

# Create the stem object
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.2, location=(0, 0, 1.6))
stem_object = bpy.context.object
stem_object.name = 'StemObject'
stem_object.data.materials.append(material_stem)


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
