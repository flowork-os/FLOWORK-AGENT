# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_sofa_in_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of sofa in blender code

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the sofa
sofa_material = bpy.data.materials.new(name="Sofa Material")
sofa_material.diffuse_color = (0.5, 0.25, 0.25, 1)  # Brownish tint

# Function to add a cube with specific properties
def add_cube(size, location, scale, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.scale = scale
    cube.name = name
    cube.data.materials.append(material)

# Add the seat
add_cube(2, (0, 0, 0.5), (2, 1, 0.2), "Seat", sofa_material)

# Add the backrest
add_cube(2, (0, -0.75, 1.1), (2, 0.1, 0.6), "Backrest", sofa_material)

# Add armrests
for index in range(2):
    position_x = 1.9 * (index * 2 - 1)
    add_cube(2, (position_x, 0, 0.75), (0.1, 1, 0.4), f"Armrest {index + 1}", sofa_material)


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
