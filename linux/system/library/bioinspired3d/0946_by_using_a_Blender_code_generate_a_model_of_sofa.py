# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_code_generate_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender code generate a model of sofa

import bpy

# Start by clearing the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the sofa
material_sofa = bpy.data.materials.new(name='SofaMaterial')
material_sofa.diffuse_color = (0.5, 0.25, 0.25, 1)

# Class to represent a sofa component
class SofaComponent:
    def __init__(self, size, location, scale, name):
        bpy.ops.mesh.primitive_cube_add(size=size, location=location)
        self.object = bpy.context.object
        self.object.scale = scale
        self.object.name = name
        self.object.data.materials.append(material_sofa)

# Create the sofa parts
base = SofaComponent(2, (0, 0, 0.5), (1.5, 0.5, 0.2), 'SofaBase')
backrest = SofaComponent(2, (0, -0.6, 1.1), (1.5, 0.1, 0.6), 'SofaBackrest')

# Create armrests using a loop
for i in range(2):
    x_position = 1.5 * (i * 2 - 1)
    SofaComponent(2, (x_position, 0, 0.75), (0.1, 0.5, 0.4), f'Armrest{i + 1}')


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
