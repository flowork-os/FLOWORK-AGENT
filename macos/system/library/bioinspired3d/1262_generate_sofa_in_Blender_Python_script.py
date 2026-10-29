# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_sofa_in_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate sofa in Blender Python script

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the sofa
sofa_material = bpy.data.materials.new(name="SofaMaterial")
sofa_material.diffuse_color = (0.5, 0.25, 0.25, 1)  # Medium brown tone

# Function to create a cube with specified parameters

def create_cube(size, location, name, scale):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(sofa_material)
    return cube

# Create the main body of the sofa
base_cuboid = create_cube(2, (0, 0, 0.5), "SofaBase", (2, 1, 0.5))

# Create the backrest of the sofa
backrest_cuboid = create_cube(2, (0, -0.75, 1.25), "SofaBackrest", (2, 0.1, 1))

# Create armrests on both sides
for index in range(2):
    armrest_position = 1.9 * (index * 2 - 1)
    create_cube(2, (armrest_position, 0, 1), f"SofaArmrest{index + 1}", (0.1, 1, 0.5))


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
