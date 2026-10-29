# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_make_a_model_of_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to make a model of sandwich.

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the sandwich components
materials = {
    'bread': (0.96, 0.87, 0.70, 1),
    'lettuce': (0.13, 0.55, 0.13, 1),
    'tomato': (0.8, 0.1, 0.1, 1),
    'cheese': (1, 0.83, 0, 1)
}

# Function to create a slice of the sandwich
def create_slice(size, location, name, mat_color):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    slice_obj = bpy.context.object
    slice_obj.scale[2] = 0.05 if 'lettuce' in name or 'tomato' in name or 'cheese' in name else 0.1
    slice_obj.name = name
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = mat_color
    slice_obj.data.materials.append(material)
    return slice_obj

# Create the sandwich layers
create_slice(2, (0, 0, 0), 'Bottom Slice', materials['bread'])
create_slice(2, (0, 0, 0.2), 'Lettuce Layer', materials['lettuce'])
create_slice(2, (0, 0, 0.3), 'Tomato Layer', materials['tomato'])
create_slice(2, (0, 0, 0.4), 'Cheese Layer', materials['cheese'])
create_slice(2, (0, 0, 0.6), 'Top Slice', materials['bread'])


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
