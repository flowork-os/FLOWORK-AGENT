# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_python_code__build_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender python code, build a model of sofa.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a function to create a sofa piece

def make_sofa_piece(size, loc, scale_factor, name):
    bpy.ops.mesh.primitive_cube_add(size=size, location=loc)
    piece = bpy.context.object
    piece.name = name
    piece.scale = scale_factor
    piece.data.materials.append(sofa_material)

# Create a material for the sofa
sofa_material = bpy.data.materials.new(name="Sofa Color")
sofa_material.diffuse_color = (0.7, 0.7, 0.7, 1)  # Light gray color

# Create the sofa base
make_sofa_piece(2, (0, 0, 0.5), (2, 1, 0.3), "Base")
# Create the backrest
make_sofa_piece(2, (0, -0.9, 1.15), (2, 0.2, 0.7), "Backrest")

# Create armrests using a loop
for arm in range(2):
    x_location = 1.9 * (arm * 2 - 1)
    make_sofa_piece(2, (x_location, 0, 0.85), (0.2, 1, 0.5), f"Armrest {arm + 1}")


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
