# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_code_in_Blender__construct_cat_scratching_post" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using code in Blender, construct cat scratching post

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the wooden texture
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Color representing wood

# Function to create a cylinder
def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(wood_material)
    return cylinder

# Generate the components of the model
create_cylinder(0.1, 2, (0, 0, 1), 'WoodenPost')
create_cylinder(0.4, 0.1, (0, 0, 0.05), 'BaseSupport')
create_cylinder(0.3, 0.05, (0, 0, 2.025), 'TopPlatform')


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
