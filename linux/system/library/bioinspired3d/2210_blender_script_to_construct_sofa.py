# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_to_construct_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script to construct sofa

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the sofa
material_sofa = bpy.data.materials.new(name='MaterialSofa')
material_sofa.diffuse_color = (0.5, 0.3, 0.2, 1)  # Earthy brown color

# Class to represent a sofa component
class SofaComponent:
    def __init__(self, name, location, scale):
        bpy.ops.mesh.primitive_cube_add(size=2, location=location)
        self.object = bpy.context.object
        self.object.name = name
        self.object.scale = scale
        self.object.data.materials.append(material_sofa)

# Create the sofa parts
base = SofaComponent('Base', (0, 0, 0.5), (3, 1, 0.5))
backrest = SofaComponent('Backrest', (0, -1, 1.5), (3, 0.2, 1))

# Create armrests
for i in range(2):
    x_position = 3 * (i * 2 - 1)
    SofaComponent(f'Armrest_{i + 1}', (x_position, 0, 1), (0.2, 1, 1))

# Create seat cushions
for i in range(3):
    x_position = 2 * (i - 1)
    SofaComponent(f'Seat_{i + 1}', (x_position, 0, 1), (0.9, 1, 0.2))


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
