# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_building_modular_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for building modular bookshelf.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a material for the structure
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.5, 0.2, 0.1, 1)

# Function to create a cube with a base

def add_cube_with_base(position):
    # Add the main cube
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    cube_object = bpy.context.object
    cube_object.name = 'Cube Unit'
    cube_object.data.materials.append(wood_material)
    
    # Calculate base position and add it
    base_position = (position[0], position[1], position[2] - 0.55)
    bpy.ops.mesh.primitive_cube_add(size=1.1, scale=(1, 1, 0.1), location=base_position)
    base_object = bpy.context.object
    base_object.name = 'Unit Base'
    base_object.data.materials.append(wood_material)

# Create a grid of cube units
for x in range(2):
    for y in range(2):
        add_cube_with_base((x * 1.2, y * 1.2, 0.5))


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
