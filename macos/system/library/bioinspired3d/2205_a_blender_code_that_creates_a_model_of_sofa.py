# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_creates_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that creates a model of sofa

import bpy

# Start with a clean slate
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the sofa
sofa_material = bpy.data.materials.new(name="Sofa Material")
sofa_material.diffuse_color = (0.5, 0.25, 0.25, 1)  # Brownish shade

# Function to add a cube with given parameters
def add_cube(name, loc, scl):
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scl
    cube.data.materials.append(sofa_material)

# Create the sofa components
add_cube("Base", (0, 0, 0.5), (2, 1, 0.2))  # Base
add_cube("Backrest", (0, -0.9, 1.1), (2, 0.2, 0.8))  # Backrest

# Adding armrests
for i in range(2):
    position = 1.9 * (i * 2 - 1)
    add_cube(f"Armrest {i + 1}", (position, 0, 0.9), (0.2, 1, 0.6))

# Adding cushions
for i in range(2):
    position = 0.9 * (i * 2 - 1)
    add_cube(f"Cushion {i + 1}", (position, 0, 0.8), (0.8, 0.9, 0.4))


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
