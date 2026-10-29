# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_python_code_that_makes_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender python code that makes pattern

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material with a specific color
material_gray = bpy.data.materials.new(name='GrayMaterial')
material_gray.diffuse_color = (0.6, 0.6, 0.6, 1)  # Lighter gray color

# Function to create cubes in a grid pattern

def create_cubes_in_grid(size, spacing):
    for x in range(-size, size + 1):
        for y in range(-size, size + 1):
            bpy.ops.mesh.primitive_cube_add(size=0.5, location=(x * spacing, y * spacing, 0))
            cube_object = bpy.context.object
            cube_object.data.materials.append(material_gray)

# Generate the grid of cubes
create_cubes_in_grid(2, 1)


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
