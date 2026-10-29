# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_code_that_creates_a_model_of_cat_scratching_post" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender code that creates a model of cat scratching post

import bpy
import math

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create the main components of the structure

# Create the base cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, -1))
base_cube = bpy.context.object
base_cube.name = 'MainBase'
base_material = bpy.data.materials.new(name='BaseColor')
base_material.diffuse_color = (0.7, 0.5, 0.3, 1)
base_cube.data.materials.append(base_material)

# Create the vertical post
bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=4, location=(0, 0, 1))
vertical_post = bpy.context.object
vertical_post.name = 'VerticalSupport'
post_material = bpy.data.materials.new(name='PostColor')
post_material.diffuse_color = (0.5, 0.3, 0.2, 1)
vertical_post.data.materials.append(post_material)

# Create the top cube
bpy.ops.mesh.primitive_cube_add(size=1.5, location=(0, 0, 3))
top_cube = bpy.context.object

# Assign the base material to the top cube
# Ensures uniform color across components
top_cube.name = 'TopCube'
top_cube.data.materials.append(base_material)


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
