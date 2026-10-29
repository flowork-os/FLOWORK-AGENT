# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_code_in_Blender_make_notebook" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with code in Blender make notebook.

import bpy
import math

# Step 1: Clear the Scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the model
cover_material = bpy.data.materials.new(name="Cover Material")
cover_material.diffuse_color = (0.1, 0.1, 0.1, 1)  # Dark gray for the cover
page_material = bpy.data.materials.new(name="Page Material")
page_material.diffuse_color = (1, 1, 1, 1)  # White for the pages
spiral_material = bpy.data.materials.new(name="Spiral Material")
spiral_material.diffuse_color = (0.5, 0.5, 0.5, 1)  # Gray for the spiral

# Function to create a cover
def create_cover(location, scale, name, material):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    cover = bpy.context.object
    cover.scale = scale
    cover.name = name
    cover.data.materials.append(material)

# Step 2: Create Covers
create_cover((0, 0, 0.1), (1, 1.5, 0.05), "Front Cover", cover_material)
create_cover((0, 0, -0.1), (1, 1.5, 0.05), "Back Cover", cover_material)

# Step 3: Create Pages
for i in range(10):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.08 - i * 0.016))
    page = bpy.context.object
    page.scale = (0.95, 1.45, 0.01)
    page.name = f"Page {i + 1}"
    page.data.materials.append(page_material)

# Step 4: Create Spiral Binding
for i in range(20):
    bpy.ops.mesh.primitive_torus_add(location=(-1.05, -1.5 + i * 0.15, 0))
    spiral = bpy.context.object
    spiral.scale = (0.05, 0.05, 0.05)
    spiral.rotation_euler = (math.pi / 2, 0, 0)
    spiral.name = f"Spiral {i + 1}"
    spiral.data.materials.append(spiral_material)


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
