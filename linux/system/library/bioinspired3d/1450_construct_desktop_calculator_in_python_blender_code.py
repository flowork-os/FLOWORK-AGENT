# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_desktop_calculator_in_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct desktop calculator in python blender code

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for different parts of the calculator
mat_black = bpy.data.materials.new(name='Black Material')
mat_black.diffuse_color = (0, 0, 0, 1)
mat_gray = bpy.data.materials.new(name='Gray Material')
mat_gray.diffuse_color = (0.5, 0.5, 0.5, 1)
mat_dark_gray = bpy.data.materials.new(name='Dark Gray Material')
mat_dark_gray.diffuse_color = (0.2, 0.2, 0.2, 1)

# Function to add a cube with material

def add_cube(size, position, scale_factors, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    cube = bpy.context.object
    cube.scale = scale_factors
    cube.data.materials.append(material)
    return cube

# Main body
calculator_body = add_cube(2, (0, 0, 0), (1, 1.5, 0.1), mat_gray)
calculator_body.name = 'Calculator Body'

# Solar panel
solar_panel = add_cube(0.4, (0, 1.3, 0.1), (1, 0.1, 0.02), mat_dark_gray)
solar_panel.name = 'Solar Panel'

# Display screen
screen = add_cube(0.6, (0, 0.9, 0.1), (1, 0.3, 0.02), mat_black)
screen.name = 'Display Screen'

# Button layout
button_coords = [(-0.6, 0.3), (-0.2, 0.3), (0.2, 0.3), (0.6, 0.3), (-0.6, 0), (-0.2, 0), (0.2, 0), (0.6, 0), (-0.6, -0.3), (-0.2, -0.3), (0.2, -0.3), (0.6, -0.3), (-0.6, -0.6), (-0.2, -0.6), (0.2, -0.6), (0.6, -0.6), (-0.6, -0.9), (-0.2, -0.9), (0.2, -0.9), (0.6, -0.9)]

for idx, (x, y) in enumerate(button_coords):
    button = add_cube(0.2, (x, y, 0.1), (0.3, 0.3, 0.05), mat_black)
    button.name = f'Button {idx + 1}'

# Clear key
clear_button = add_cube(0.2, (0.6, 0.6, 0.1), (0.3, 0.3, 0.05), mat_black)
clear_button.name = 'Clear Key'


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
