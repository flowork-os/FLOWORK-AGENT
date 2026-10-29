# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_code_create_cat_scratching_post" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender code create cat scratching post.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cylinder

def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    return obj

# Create the base
base_cylinder = create_cylinder(0.45, 0.1, (0, 0, 0), 'Base')

# Create the post
post_cylinder = create_cylinder(0.1, 0.6, (0, 0, 0.35), 'Post')

# Create the platform
bpy.ops.mesh.primitive_cube_add(size=0.3, location=(0, 0, 0.65))
platform_cube = bpy.context.object
platform_cube.name = 'Platform'

# Create and assign material to the post
post_material = bpy.data.materials.new(name='EarthyMaterial')
post_material.diffuse_color = (0.4, 0.2, 0.1, 1)  # A different shade of brown
post_cylinder.data.materials.append(post_material)


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
