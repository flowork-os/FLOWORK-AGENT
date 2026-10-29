# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_umbrella_using_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of umbrella using a Blender code

import bpy
import math

# Remove all mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material
material_dark = bpy.data.materials.new(name='JetBlack')
material_dark.diffuse_color = (0.0, 0.0, 0.0, 1)

# Function to create a primitive

def create_primitive(type, params, name):
    if type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(**params)
    elif type == 'cone':
        bpy.ops.mesh.primitive_cone_add(**params)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material_dark)
    return obj

# Create each component
create_primitive('cylinder', {'radius': 0.05, 'depth': 0.2, 'location': (0, 0, -0.1)}, 'Handle')
create_primitive('cylinder', {'radius': 0.02, 'depth': 0.02, 'location': (0, 0.05, 0)}, 'Button')
create_primitive('cylinder', {'radius': 0.02, 'depth': 1.0, 'location': (0, 0, 0.5)}, 'Shaft')
create_primitive('cone', {'vertices': 16, 'radius1': 0.6, 'radius2': 0.02, 'depth': 0.7, 'location': (0, 0, 1.2)}, 'Canopy')

# Modify the canopy to appear folded
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.transform.shrink_fatten(value=-0.3)
bpy.ops.object.mode_set(mode='OBJECT')


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
