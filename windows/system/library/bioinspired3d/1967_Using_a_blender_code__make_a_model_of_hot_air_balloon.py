# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_a_blender_code__make_a_model_of_hot_air_balloon" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using a blender code, make a model of hot air balloon.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Set up materials for the balloon, basket, and ropes
mat_balloon = bpy.data.materials.new(name='Balloon Material')
mat_balloon.diffuse_color = (0.9, 0.1, 0.1, 1)
mat_basket = bpy.data.materials.new(name='Basket Material')
mat_basket.diffuse_color = (0.6, 0.3, 0.1, 1)
mat_rope = bpy.data.materials.new(name='Rope Material')
mat_rope.diffuse_color = (0.85, 0.85, 0.85, 1)

# Create a balloon
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 2))
balloon = bpy.context.object
balloon.name = 'Balloon'
balloon.data.materials.append(mat_balloon)

# Create a basket
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0, 0))
basket = bpy.context.object
basket.name = 'Basket'
basket.data.materials.append(mat_basket)

# Create the ropes using a list of locations
rope_locations = [(0.3, 0.3, 1), (-0.3, 0.3, 1), (0.3, -0.3, 1), (-0.3, -0.3, 1)]
for loc in rope_locations:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=2, location=loc)
    rope = bpy.context.object
    rope.name = 'Rope'
    rope.data.materials.append(mat_rope)


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
