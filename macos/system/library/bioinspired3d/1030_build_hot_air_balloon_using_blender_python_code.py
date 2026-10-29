# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_hot_air_balloon_using_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build hot air balloon using blender python code

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for different components
material_balloon = bpy.data.materials.new(name='Material for Balloon')
material_balloon.diffuse_color = (1, 0.2, 0.2, 1)  # Bright red
material_basket = bpy.data.materials.new(name='Material for Basket')
material_basket.diffuse_color = (0.4, 0.2, 0.1, 1)  # Darker brown
material_rope = bpy.data.materials.new(name='Material for Rope')
material_rope.diffuse_color = (0.9, 0.9, 0.9, 1)  # Light gray

# Create balloon geometry
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 2))
balloon_object = bpy.context.object
balloon_object.name = 'Balloon'
balloon_object.data.materials.append(material_balloon)

# Create basket geometry
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0, 0))
basket_object = bpy.context.object
basket_object.name = 'Basket'
basket_object.data.materials.append(material_basket)

# Generate ropes
rope_coords = [(0.3, 0.3, 1), (-0.3, 0.3, 1), (0.3, -0.3, 1), (-0.3, -0.3, 1)]
for coords in rope_coords:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=2, location=coords)
    rope_object = bpy.context.object
    rope_object.name = 'Rope'
    rope_object.data.materials.append(material_rope)


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
