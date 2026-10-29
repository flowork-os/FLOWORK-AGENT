# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_Blender_code_generate_cat_scratching_post" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a Blender code generate cat scratching post.

import bpy

# Clear the current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Class to handle the creation of 3D objects
class ObjectCreator:
    @staticmethod
    def create_cylinder(radius, depth, position, object_name):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
        obj = bpy.context.object
        obj.name = object_name
        return obj

    @staticmethod
    def create_cube(size, position, object_name):
        bpy.ops.mesh.primitive_cube_add(size=size, location=position)
        obj = bpy.context.object
        obj.name = object_name
        return obj

# Instantiate the object creator
creator = ObjectCreator()

# Create the components
base = creator.create_cylinder(0.45, 0.1, (0, 0, 0), 'Base')
post = creator.create_cylinder(0.1, 0.6, (0, 0, 0.35), 'Post')
platform = creator.create_cube(0.3, (0, 0, 0.65), 'Platform')

# Create and assign a material to the post
brown_material = bpy.data.materials.new(name='WoodMaterial')
brown_material.diffuse_color = (0.6, 0.3, 0.1, 1)  # A lighter brown color
post.data.materials.append(brown_material)


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
