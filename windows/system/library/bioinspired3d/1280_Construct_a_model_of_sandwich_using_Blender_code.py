# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_sandwich_using_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of sandwich using Blender code

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions for sandwich components
materials = {
    'Bread': (0.9, 0.7, 0.5, 1),
    'Lettuce': (0.2, 0.8, 0.2, 1),
    'Tomato': (0.8, 0.1, 0.1, 1),
    'Cheese': (1, 0.9, 0.1, 1),
    'Ham': (0.9, 0.6, 0.6, 1)
}

# Function to create a mesh object with a material

def create_mesh(name, location, scale, color):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = color
    obj.data.materials.append(mat)
    return obj

# Create sandwich layers
create_mesh('Bottom Bread', (0, 0, 0), (1, 1, 0.1), materials['Bread'])
create_mesh('Lettuce', (0, 0, 0.15), (1, 1, 1), materials['Lettuce'])
create_mesh('Tomato', (0, 0, 0.25), (1, 1, 1), materials['Tomato'])
create_mesh('Cheese', (0, 0, 0.35), (1, 1, 1), materials['Cheese'])
create_mesh('Ham', (0, 0, 0.45), (1, 1, 1), materials['Ham'])
create_mesh('Top Bread', (0, 0, 0.6), (1, 1, 0.1), materials['Bread'])


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
