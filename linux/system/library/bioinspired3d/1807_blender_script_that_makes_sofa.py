# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_makes_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that makes sofa.

import bpy

# Clear existing mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the sofa
sofa_material = bpy.data.materials.new(name="SofaMaterial")
sofa_material.diffuse_color = (0.4, 0.2, 0.2, 1)  # Darker brown color

# Function to create a cube with specific properties
def create_cube(size, location, scale, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.scale = scale
    cube.name = name
    cube.data.materials.append(material)
    return cube

# Build the sofa components
create_cube(2, (0, 0, 0.5), (2, 1, 0.2), "SofaBase", sofa_material)
create_cube(2, (0, -0.9, 1.1), (2, 0.2, 0.7), "SofaBackrest", sofa_material)

# Create armrests
for index in range(2):
    create_cube(2, (2 * (index * 2 - 1), 0, 0.75), (0.2, 1, 0.5), f"SofaArmrest{index + 1}", sofa_material)

# Create cushions
for index in range(3):
    create_cube(2, ((index - 1) * 1.5, 0, 0.75), (0.5, 1, 0.2), f"SofaCushion{index + 1}", sofa_material)


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
