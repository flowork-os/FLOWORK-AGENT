# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_sofa_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of sofa in blender python code

import bpy

# Clear the existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the sofa
sofa_material = bpy.data.materials.new(name="SofaMaterial")
sofa_material.diffuse_color = (0.5, 0.25, 0.1, 1)

# Function to create a cube with specific properties

def create_cube(size, location, name, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(material)

# Construct the sofa base
create_cube(2, (0, 0, 0.5), "Sofa Base", (3, 1, 0.5), sofa_material)

# Construct the backrest
create_cube(2, (0, -0.95, 1.25), "Backrest", (3, 0.1, 0.75), sofa_material)

# Construct the armrests
for idx in range(2):
    armrest_x = 3 * (idx * 2 - 1)
    create_cube(2, (armrest_x, 0, 0.75), f"Armrest {idx + 1}", (0.1, 1, 0.75), sofa_material)

# Construct the storage section
create_cube(2, (0, 0, -0.25), "Storage", (3, 1, 0.25), sofa_material)


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
