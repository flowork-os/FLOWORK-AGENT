# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_blender_code_construct_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a blender code construct a model of sofa

import bpy

# Clear the existing mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the sofa
sofa_material = bpy.data.materials.new(name="Sofa Material")
sofa_material.diffuse_color = (0.2, 0.2, 0.2, 1)  # Dark gray

# Function to create a cube with specified parameters
def create_cube(name, location, scale):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(sofa_material)
    return cube

# Create the seat of the sofa
create_cube("Seat", (0, 0, 0.5), (3, 1, 0.5))

# Create the backrest of the sofa
create_cube("Backrest", (0, -1, 1.25), (3, 0.2, 1))

# Create the armrests
for i in range(2):
    position_x = 3 * (i * 2 - 1)
    create_cube(f"Armrest {i + 1}", (position_x, 0, 0.75), (0.2, 1, 0.75))


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
