# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_that_creates_a_model_of_notebook" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code that creates a model of notebook

import bpy
import math

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials
cover_mat = bpy.data.materials.new(name="Cover")
cover_mat.diffuse_color = (0.1, 0.1, 0.1, 1)
page_mat = bpy.data.materials.new(name="Page")
page_mat.diffuse_color = (1, 1, 1, 1)
spiral_mat = bpy.data.materials.new(name="Spiral")
spiral_mat.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to add a cube for the cover
def add_cover(position, dimensions, title, material):
    bpy.ops.mesh.primitive_cube_add(size=2, location=position)
    cube = bpy.context.object
    cube.scale = dimensions
    cube.name = title
    cube.data.materials.append(material)

# Generate covers
add_cover((0, 0, 0.1), (1, 1.5, 0.05), "Front Cover", cover_mat)
add_cover((0, 0, -0.1), (1, 1.5, 0.05), "Back Cover", cover_mat)

# Create pages
for idx in range(10):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.08 - idx * 0.016))
    page = bpy.context.object
    page.scale = (0.95, 1.45, 0.01)
    page.name = f"Page {idx + 1}"
    page.data.materials.append(page_mat)

# Generate spiral binding
for idx in range(20):
    bpy.ops.mesh.primitive_torus_add(location=(-1.05, -1.5 + idx * 0.15, 0))
    spiral = bpy.context.object
    spiral.scale = (0.05, 0.05, 0.05)
    spiral.rotation_euler = (math.pi / 2, 0, 0)
    spiral.name = f"Spiral {idx + 1}"
    spiral.data.materials.append(spiral_mat)


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
