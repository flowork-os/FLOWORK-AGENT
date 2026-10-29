# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_creating_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for creating a model of sofa

import bpy

# Clear the scene of any mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a sofa material
sofa_material = bpy.data.materials.new(name="SofaMaterial")
sofa_material.diffuse_color = (0.5, 0.25, 0.25, 1)  # Color for the sofa

# Create base, backrest, and armrests in a single function

def build_sofa():
    # Base
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
    base = bpy.context.object
    base.name = "SofaBase"
    base.scale = (2, 1, 0.5)
    base.data.materials.append(sofa_material)

    # Backrest
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, -0.75, 1.25))
    backrest = bpy.context.object
    backrest.name = "SofaBackrest"
    backrest.scale = (2, 0.1, 1)
    backrest.data.materials.append(sofa_material)

    # Armrests
    for i in range(2):
        x = 1.9 * (i * 2 - 1)
        bpy.ops.mesh.primitive_cube_add(size=2, location=(x, 0, 1))
        armrest = bpy.context.object
        armrest.name = f"SofaArmrest {i + 1}"
        armrest.scale = (0.1, 1, 0.5)
        armrest.data.materials.append(sofa_material)

# Call the function to build the sofa
build_sofa()


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
