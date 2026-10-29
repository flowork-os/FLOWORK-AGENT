# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_sofa_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of sofa in a Blender script

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create the sofa material
material_sofa = bpy.data.materials.new(name="Sofa Texture")
material_sofa.diffuse_color = (0.5, 0.25, 0.25, 1)  # Dark brown shade

# Function to create a sofa piece

def create_sofa_piece(size, loc, scale_factors, piece_name):
    bpy.ops.mesh.primitive_cube_add(size=size, location=loc)
    piece = bpy.context.object
    piece.scale = scale_factors
    piece.name = piece_name
    piece.data.materials.append(material_sofa)

# Construct the sofa components
create_sofa_piece(2, (0, 0, 0.5), (2, 1, 0.2), "Seat")
create_sofa_piece(2, (0, -0.75, 1.1), (2, 0.1, 0.6), "Backrest")

# Create armrests using a loop
for i in range(2):
    armrest_x = 1.9 * (i * 2 - 1)
    create_sofa_piece(2, (armrest_x, 0, 0.75), (0.1, 1, 0.4), f"Armrest {i + 1}")


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
