# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_script_to_create_notebook" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender script to create notebook

import bpy
import math

# Clear the current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials for the model
cover_col = bpy.data.materials.new(name="Cover Color")
cover_col.diffuse_color = (0.1, 0.1, 0.1, 1)
page_col = bpy.data.materials.new(name="Page Color")
page_col.diffuse_color = (1, 1, 1, 1)
spiral_col = bpy.data.materials.new(name="Spiral Color")
spiral_col.diffuse_color = (0.5, 0.5, 0.5, 1)

# Create covers using a helper function
def create_cube(location, scale_factors, obj_name, mat):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    cube_obj = bpy.context.object
    cube_obj.scale = scale_factors
    cube_obj.name = obj_name
    cube_obj.data.materials.append(mat)

# Create the front and back covers
create_cube((0, 0, 0.1), (1, 1.5, 0.05), "Front Cover", cover_col)
create_cube((0, 0, -0.1), (1, 1.5, 0.05), "Back Cover", cover_col)

# Add pages to the model
for index in range(10):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.08 - index * 0.016))
    page_obj = bpy.context.object
    page_obj.scale = (0.95, 1.45, 0.01)
    page_obj.name = f"Page {index + 1}"
    page_obj.data.materials.append(page_col)

# Create spiral binding
for index in range(20):
    bpy.ops.mesh.primitive_torus_add(location=(-1.05, -1.5 + index * 0.15, 0))
    spiral_obj = bpy.context.object
    spiral_obj.scale = (0.05, 0.05, 0.05)
    spiral_obj.rotation_euler = (math.pi / 2, 0, 0)
    spiral_obj.name = f"Spiral {index + 1}"
    spiral_obj.data.materials.append(spiral_col)


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
