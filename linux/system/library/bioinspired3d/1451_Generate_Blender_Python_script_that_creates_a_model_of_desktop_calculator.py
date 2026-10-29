# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_Python_script_that_creates_a_model_of_desktop_calculator" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender Python script that creates a model of desktop calculator.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions
black_material = bpy.data.materials.new(name='Black')
black_material.diffuse_color = (0, 0, 0, 1)
grey_material = bpy.data.materials.new(name='Grey')
grey_material.diffuse_color = (0.5, 0.5, 0.5, 1)
dark_grey_material = bpy.data.materials.new(name='Dark Grey')
dark_grey_material.diffuse_color = (0.2, 0.2, 0.2, 1)

# Class for creating calculator components
class CalculatorComponent:
    def __init__(self, size, location, scale, material, name):
        bpy.ops.mesh.primitive_cube_add(size=size, location=location)
        self.object = bpy.context.object
        self.object.scale = scale
        self.object.data.materials.append(material)
        self.object.name = name

# Create components
body = CalculatorComponent(2, (0, 0, 0), (1, 1.5, 0.1), grey_material, 'Calculator Body')
solar_panel = CalculatorComponent(0.4, (0, 1.3, 0.1), (1, 0.1, 0.02), dark_grey_material, 'Solar Panel')
display = CalculatorComponent(0.6, (0, 0.9, 0.1), (1, 0.3, 0.02), black_material, 'Display Screen')

# Button coordinates
button_coords = [(-0.6, 0.3), (-0.2, 0.3), (0.2, 0.3), (0.6, 0.3), (-0.6, 0), (-0.2, 0), (0.2, 0), (0.6, 0), (-0.6, -0.3), (-0.2, -0.3), (0.2, -0.3), (0.6, -0.3), (-0.6, -0.6), (-0.2, -0.6), (0.2, -0.6), (0.6, -0.6), (-0.6, -0.9), (-0.2, -0.9), (0.2, -0.9), (0.6, -0.9)]

for idx, (x, y) in enumerate(button_coords):
    CalculatorComponent(0.2, (x, y, 0.1), (0.3, 0.3, 0.05), black_material, f'Button {idx + 1}')

# Clear key
CalculatorComponent(0.2, (0.6, 0.6, 0.1), (0.3, 0.3, 0.05), black_material, 'Clear Key')


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
