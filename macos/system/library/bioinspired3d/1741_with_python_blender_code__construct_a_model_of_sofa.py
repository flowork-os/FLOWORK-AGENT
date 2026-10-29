# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_python_blender_code__construct_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with python blender code, construct a model of sofa.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a new material for the chair
chair_material = bpy.data.materials.new(name='Chair Material')
chair_material.diffuse_color = (0.9, 0.9, 0.9, 1)  # Very light gray

# Class to represent a chair component
class ChairComponent:
    def __init__(self, size, location, scale, name, material):
        bpy.ops.mesh.primitive_cube_add(size=size, location=location)
        component = bpy.context.object
        component.scale = scale
        component.name = name
        component.data.materials.append(material)

# Create chair parts
ChairComponent(2, (0, 0, 0.5), (2, 1, 0.2), 'Main Seat', chair_material)
ChairComponent(2, (0, -0.75, 1.2), (2, 0.2, 0.7), 'Back Support', chair_material)

# Adding armrests
for arm_index in range(2):
    arm_x = 2 * (arm_index * 2 - 1)
    ChairComponent(2, (arm_x, 0, 0.75), (0.2, 1, 0.5), f'Armrest {arm_index + 1}', chair_material)


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
