# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_for_making_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code for making sofa.

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the sofa and cushions
sofa_material = bpy.data.materials.new(name="SofaMaterial")
sofa_material.diffuse_color = (0.5, 0.25, 0.25, 1)

cushion_material = bpy.data.materials.new(name="CushionMaterial")
cushion_material.diffuse_color = (0.8, 0.8, 0.8, 1)

# Function to create a cube with specified parameters

def create_cube(location, scale, name, material):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    cube = bpy.context.object
    cube.scale = scale
    cube.name = name
    cube.data.materials.append(material)

# Create the sofa base
create_cube((0, 0, 0.5), (2, 1, 0.5), "SofaBase", sofa_material)

# Create the backrest
create_cube((0, -0.75, 1.25), (2, 0.25, 0.75), "Backrest", sofa_material)

# Create seat cushions
for index in range(3):
    create_cube((-1.25 + index * 1.25, 0, 1), (0.6, 0.9, 0.2), f"SeatCushion_{index + 1}", cushion_material)

# Create backrest cushions
for index in range(3):
    create_cube((-1.25 + index * 1.25, -0.75, 1.75), (0.6, 0.2, 0.5), f"BackrestCushion_{index + 1}", cushion_material)


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
