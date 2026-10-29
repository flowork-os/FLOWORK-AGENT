# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_code_to_create_a_model_of_calculator" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender code to create a model of calculator

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the calculator components
material_calculator = bpy.data.materials.new(name='CalculatorMaterial')
material_calculator.diffuse_color = (0.1, 0.1, 0.1, 1)
material_buttons = bpy.data.materials.new(name='ButtonsMaterial')
material_buttons.diffuse_color = (0.8, 0.8, 0.8, 1)
material_display = bpy.data.materials.new(name='DisplayMaterial')
material_display.diffuse_color = (0.2, 0.8, 0.2, 1)

# Create a calculator body
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
calculator_body = bpy.context.object
calculator_body.name = 'CalculatorBody'
calculator_body.scale = (1, 1.5, 0.1)
calculator_body.data.materials.append(material_calculator)

# Create the display screen
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 1.2, 0.1))
screen = bpy.context.object
screen.name = 'Screen'
screen.scale = (0.8, 0.3, 0.05)
screen.data.materials.append(material_display)

# Define button positions
button_positions = [(-0.6, -0.6), (-0.2, -0.6), (0.2, -0.6), (0.6, -0.6),
                    (-0.6, -0.2), (-0.2, -0.2), (0.2, -0.2), (0.6, -0.2),
                    (-0.6, 0.2), (-0.2, 0.2), (0.2, 0.2), (0.6, 0.2),
                    (-0.6, 0.6), (-0.2, 0.6), (0.2, 0.6), (0.6, 0.6)]

# Create buttons at specified positions
for idx, (x, y) in enumerate(button_positions):
    bpy.ops.mesh.primitive_cube_add(size=0.4, location=(x, y, 0.1))
    button = bpy.context.object
    button.name = f'Button_{idx + 1}'
    button.scale = (0.3, 0.3, 0.05)
    button.data.materials.append(material_buttons)


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
