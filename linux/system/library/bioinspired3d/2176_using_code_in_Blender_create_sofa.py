# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_code_in_Blender_create_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using code in Blender create sofa.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the sofa
sofa_material = bpy.data.materials.new(name='Sofa Material')
sofa_material.diffuse_color = (0.5, 0.25, 0.25, 1)

# Function to create a cube with specific properties
def create_cube(name, location, scale):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(sofa_material)
    return cube

# Build the sofa base
create_cube('Sofa Base', (0, 0, 0.5), (2, 1, 0.2))

# Build the backrest
create_cube('Backrest', (0, -0.9, 1.1), (2, 0.2, 0.6))

# Create armrests
for index in range(2):
    position_x = 2 * (index * 2 - 1)
    create_cube(f'Armrest {index + 1}', (position_x, 0, 0.75), (0.2, 1, 0.5))

# Create cushions
for index in range(3):
    position_x = (index - 1) * 1.3
    create_cube(f'Cushion {index + 1}', (position_x, 0, 0.75), (0.6, 1, 0.2))


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
