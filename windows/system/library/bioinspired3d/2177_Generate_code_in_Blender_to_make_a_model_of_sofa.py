# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_code_in_Blender_to_make_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate code in Blender to make a model of sofa.

import bpy

# Remove all mesh objects in the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Sofa color definition
brown_color = bpy.data.materials.new(name='Brown Sofa')
brown_color.diffuse_color = (0.5, 0.25, 0.25, 1)

# Create the sofa components using a class
class Sofa:
    def __init__(self):
        self.material = brown_color

    def add_component(self, name, location, scale):
        bpy.ops.mesh.primitive_cube_add(size=2, location=location)
        component = bpy.context.object
        component.name = name
        component.scale = scale
        component.data.materials.append(self.material)

sofa = Sofa()

# Add base
sofa.add_component('Sofa Base', (0, 0, 0.5), (2, 1, 0.2))

# Add backrest
sofa.add_component('Backrest', (0, -0.9, 1.1), (2, 0.2, 0.6))

# Add armrests
for idx in range(2):
    sofa.add_component(f'Armrest {idx + 1}', (2 * (idx * 2 - 1), 0, 0.75), (0.2, 1, 0.5))

# Add cushions
for idx in range(3):
    sofa.add_component(f'Cushion {idx + 1}', ((idx - 1) * 1.3, 0, 0.75), (0.6, 1, 0.2))


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
