# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_blender_code_generate_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a blender code generate sandwich.

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the sandwich components
materials = {
    'bread': (0.9, 0.7, 0.5, 1),
    'lettuce': (0.2, 0.8, 0.2, 1),
    'tomato': (0.8, 0.1, 0.1, 1),
    'cheese': (1, 0.9, 0.1, 1)
}

# Function to create a cube with a specific material
def create_cube(name, location, scale, material_color):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale[2] = scale
    mat = bpy.data.materials.new(name=name + " Material")
    mat.diffuse_color = material_color
    cube.data.materials.append(mat)
    return cube

# Construct the sandwich layers
create_cube("Bottom Bread", (0, 0, 0), 0.1, materials['bread'])
create_cube("Lettuce", (0, 0, 0.2), 0.05, materials['lettuce'])
create_cube("Tomato", (0, 0, 0.3), 0.1, materials['tomato'])
create_cube("Cheese", (0, 0, 0.4), 0.05, materials['cheese'])
create_cube("Top Bread", (0, 0, 0.6), 0.1, materials['bread'])


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
