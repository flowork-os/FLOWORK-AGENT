# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_that_creates_cat_scratching_post" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code that creates cat scratching post.

import bpy

# Function to clear the scene of mesh objects

def clear_scene():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

# Clear the scene
clear_scene()

# Create base, post, and platform using different parameters
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.1, location=(0, 0, 0))
base_obj = bpy.context.object
base_obj.name = 'Base'

bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=(0, 0, 0.4))
post_obj = bpy.context.object
post_obj.name = 'Post'

bpy.ops.mesh.primitive_cube_add(size=0.35, location=(0, 0, 0.7))
platform_obj = bpy.context.object
platform_obj.name = 'Platform'

# Assign a new material to the post
material_post = bpy.data.materials.new(name='TexturedMaterial')
material_post.diffuse_color = (0.55, 0.2, 0.1, 1)  # A different brown hue
post_obj.data.materials.append(material_post)


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
