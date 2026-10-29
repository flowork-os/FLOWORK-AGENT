# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_build_a_model_of_umbrella" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to build a model of umbrella

import bpy
import math

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a black material
material_black = bpy.data.materials.new(name='BlackMaterial')
material_black.diffuse_color = (0.0, 0.0, 0.0, 1)

# Class to create components of the model
class ModelComponent:
    def __init__(self, shape_func, params, name):
        shape_func(**params)
        self.object = bpy.context.object
        self.object.name = name
        self.object.data.materials.append(material_black)

# Create components
ModelComponent(bpy.ops.mesh.primitive_cylinder_add, {'radius': 0.05, 'depth': 0.2, 'location': (0, 0, -0.1)}, 'Handle')
ModelComponent(bpy.ops.mesh.primitive_cylinder_add, {'radius': 0.02, 'depth': 0.02, 'location': (0, 0.05, 0)}, 'Button')
ModelComponent(bpy.ops.mesh.primitive_cylinder_add, {'radius': 0.02, 'depth': 1.0, 'location': (0, 0, 0.5)}, 'Shaft')

# Create the canopy
bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.6, radius2=0.02, depth=0.7, location=(0, 0, 1.2))
canopy = bpy.context.object
canopy.name = 'Canopy'
canopy.data.materials.append(material_black)

# Edit the canopy shape
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
