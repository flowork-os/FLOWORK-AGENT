# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_python_blender_code__build_cat_scratching_post" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using python blender code, build cat scratching post.

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cube base

def create_base(size, location):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = 'CubeBase'
    material = bpy.data.materials.new(name='CubeMaterial')
    material.diffuse_color = (0.7, 0.5, 0.3, 1)
    cube.data.materials.append(material)
    return cube

# Function to create a cylindrical post

def create_post(radius, height, location):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=location)
    cylinder = bpy.context.object
    cylinder.name = 'CylinderPost'
    material = bpy.data.materials.new(name='CylinderMaterial')
    material.diffuse_color = (0.5, 0.3, 0.2, 1)
    cylinder.data.materials.append(material)
    return cylinder

# Create the base, post, and top platform
base = create_base(2, (0, 0, -1))
post = create_post(0.3, 4, (0, 0, 1))
bpy.ops.mesh.primitive_cube_add(size=1.5, location=(0, 0, 3))
top_platform = bpy.context.object

# Assigning the same material from the base to the top platform
# This maintains consistent appearance

top_platform.name = 'TopPlatform'
top_platform.data.materials.append(base.data.materials[0])


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
