# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_cat_scratching_post_using_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct cat scratching post using a blender code

import bpy

# Clear the existing mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the wooden appearance
wooden_texture = bpy.data.materials.new(name='WoodenTexture')
wooden_texture.diffuse_color = (0.55, 0.27, 0.07, 1)  # Shade of brown for wood

# Function to add a cylinder with material
def add_cylinder(radius, height, position, obj_name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    obj = bpy.context.object
    obj.name = obj_name
    obj.data.materials.append(wooden_texture)

# Build the structure components
add_cylinder(0.1, 2, (0, 0, 1), 'VerticalPost')
add_cylinder(0.4, 0.1, (0, 0, 0.05), 'SupportBase')
add_cylinder(0.3, 0.05, (0, 0, 2.025), 'TopSurface')


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
