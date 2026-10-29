# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_sofa_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate sofa in blender python code

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a brown material for the sofa
brown_sofa_material = bpy.data.materials.new(name='BrownSofa')
brown_sofa_material.diffuse_color = (0.5, 0.25, 0.25, 1)  # Standard brown color

# Class to represent a Sofa
class Sofa:
    def __init__(self, material):
        self.material = material

    def create_part(self, size, location, name, scale):
        bpy.ops.mesh.primitive_cube_add(size=size, location=location)
        part = bpy.context.object
        part.name = name
        part.scale = scale
        part.data.materials.append(self.material)

# Instantiate the Sofa class
sofa = Sofa(brown_sofa_material)

# Create the sofa components
sofa.create_part(2, (0, 0, 0.5), 'SofaBase', (2, 1, 0.2))
sofa.create_part(2, (0, -0.9, 1.1), 'SofaBackrest', (2, 0.1, 0.6))

# Create armrests
for armrest_index in range(2):
    x_position = 1.9 * (armrest_index * 2 - 1)
    sofa.create_part(2, (x_position, 0, 0.7), f'SofaArmrest{armrest_index + 1}', (0.1, 1, 0.4))


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
