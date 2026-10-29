# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_Blender_code__create_a_model_of_apple" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using Blender code, create a model of apple.

import bpy

# Clear the current mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials for apple and stem
mat_apple = bpy.data.materials.new(name='Apple Red')
mat_apple.diffuse_color = (0.8, 0.1, 0.1, 1)

mat_stem = bpy.data.materials.new(name='Stem Brown')
mat_stem.diffuse_color = (0.4, 0.2, 0.1, 1)

# Create apple geometry
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
apple = bpy.context.object
apple.name = 'Apple'
apple.data.materials.append(mat_apple)

# Create stem geometry
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.3, location=(0, 0, 1.15))
stem = bpy.context.object
stem.name = 'Stem'
stem.data.materials.append(mat_stem)

# Group objects into a collection
collection = bpy.data.collections.new('Fruit Collection')
bpy.context.scene.collection.children.link(collection)
collection.objects.link(apple)
collection.objects.link(stem)


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
