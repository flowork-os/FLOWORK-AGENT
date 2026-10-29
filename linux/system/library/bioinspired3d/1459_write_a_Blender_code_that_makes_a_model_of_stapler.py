# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_code_that_makes_a_model_of_stapler" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender code that makes a model of stapler.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the stapler
mat_body = bpy.data.materials.new(name='Main Body Color')
mat_body.diffuse_color = (0.15, 0.15, 0.15, 1)  # A shade of gray
mat_lever = bpy.data.materials.new(name='Top Lever Color')
mat_lever.diffuse_color = (0.85, 0.85, 0.85, 1)  # A lighter shade

# Create the main components of the stapler
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
main_part = bpy.context.object
main_part.name = 'Main Body'
main_part.scale = (1, 0.3, 0.2)
main_part.data.materials.append(mat_body)

bpy.ops.mesh.primitive_cube_add(size=1.8, location=(0, 0, 0.3))
lever_part = bpy.context.object
lever_part.name = 'Top Lever'
lever_part.scale = (1, 0.25, 0.1)
lever_part.data.materials.append(mat_lever)


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
