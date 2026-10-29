# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_sofa_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of sofa using code in Blender

import bpy

# Clear all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a material for the cushions
cushion_material = bpy.data.materials.new(name="Cushion Color")
cushion_material.diffuse_color = (0.8, 0.2, 0.2, 1)

# Create the seat geometry
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
seat = bpy.context.object
seat.name = "Seat"
seat.scale = (2, 1, 0.2)
seat.data.materials.append(cushion_material)

# Create the backrest geometry
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, -1.1, 1.2))
backrest = bpy.context.object
backrest.name = "Backrest"
backrest.scale = (2, 0.2, 1)
backrest.data.materials.append(cushion_material)

# Create armrests in a loop
for i in range(2):
    x_position = 2.1 * (i * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, 1))
    armrest = bpy.context.object
    armrest.name = f"Armrest {i + 1}"
    armrest.scale = (0.2, 1, 0.5)
    armrest.data.materials.append(cushion_material)


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
