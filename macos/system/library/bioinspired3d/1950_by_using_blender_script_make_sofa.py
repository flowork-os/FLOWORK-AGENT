# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_blender_script_make_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using blender script make sofa.

import bpy
import math

# Clear the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the sofa
sofa_material = bpy.data.materials.new(name="Sofa Material")
sofa_material.diffuse_color = (0.4, 0.2, 0.2, 1)  # Darker brown shade

# Function to create a cube with specified parameters
def create_cube(name, location, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(material)

# Create the seat
create_cube("Seat", (0, 0, 0.5), (2, 1, 0.2), sofa_material)

# Create the backrest
create_cube("Backrest", (0, -1.1, 1.2), (2, 0.2, 0.8), sofa_material)

# Create the armrests
for index in range(2):
    position_x = 2 * (index * 2 - 1)  # Calculate x position
    create_cube(f"Armrest {index + 1}", (position_x, 0, 0.9), (0.2, 1, 0.6), sofa_material)


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
