# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_code_make_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender code make sofa

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the model
material_gray = bpy.data.materials.new(name='Gray Material')
material_gray.diffuse_color = (0.7, 0.7, 0.7, 1)  # Soft gray color

# Function to create a cube with specific parameters
def create_cube(size, location, scale, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.scale = scale
    cube.name = name
    cube.data.materials.append(material)

# Construct the main components of the chair
create_cube(2, (0, 0, 0.5), (2, 1, 0.2), 'Seat Base', material_gray)  # Base
create_cube(2, (0, -0.75, 1.2), (2, 0.2, 0.7), 'Chair Backrest', material_gray)  # Backrest

# Create armrests using a loop
for index in range(2):
    position_x = 2 * (index * 2 - 1)
    create_cube(2, (position_x, 0, 0.75), (0.2, 1, 0.5), f'Armrest {index + 1}', material_gray)  # Armrests


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
