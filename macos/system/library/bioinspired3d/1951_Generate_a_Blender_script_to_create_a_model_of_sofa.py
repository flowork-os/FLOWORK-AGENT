# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_script_to_create_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender script to create a model of sofa.

import bpy

# Reset the scene by removing all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a new material for the sofa
sofa_texture = bpy.data.materials.new(name="Sofa Texture")
sofa_texture.diffuse_color = (0.6, 0.3, 0.3, 1)  # Lighter brown

# Create the seat geometry
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
seat = bpy.context.object
seat.name = "Seat"
seat.scale[0] = 2.0
seat.scale[1] = 1.0
seat.scale[2] = 0.2
seat.data.materials.append(sofa_texture)

# Create the backrest geometry
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, -1.1, 1.2))
backrest = bpy.context.object
backrest.name = "Backrest"
backrest.scale[0] = 2.0
backrest.scale[1] = 0.2
backrest.scale[2] = 0.8
backrest.data.materials.append(sofa_texture)

# Create armrests with a loop
for i in range(2):
    armrest_x = 2 * (i * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(armrest_x, 0, 0.9))
    armrest = bpy.context.object
    armrest.name = f"Armrest {i + 1}"
    armrest.scale[0] = 0.2
    armrest.scale[1] = 1.0
    armrest.scale[2] = 0.6
    armrest.data.materials.append(sofa_texture)


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
