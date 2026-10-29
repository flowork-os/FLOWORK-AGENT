# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_desktop_calculator_in_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate desktop calculator in a Blender code

import bpy

# Clear the existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the calculator
material_black = bpy.data.materials.new(name='Material Black')
material_black.diffuse_color = (0, 0, 0, 1)
material_gray = bpy.data.materials.new(name='Material Gray')
material_gray.diffuse_color = (0.5, 0.5, 0.5, 1)
material_dark_gray = bpy.data.materials.new(name='Material Dark Gray')
material_dark_gray.diffuse_color = (0.2, 0.2, 0.2, 1)

# Function to create a cube with given parameters

def create_cube(size, location, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.scale = scale
    cube.data.materials.append(material)
    return cube

# Create the main body of the calculator
body = create_cube(2, (0, 0, 0), (1, 1.5, 0.1), material_gray)
body.name = 'Calculator Body'

# Create the solar panel
solar_panel = create_cube(0.4, (0, 1.3, 0.1), (1, 0.1, 0.02), material_dark_gray)
solar_panel.name = 'Solar Panel'

# Create the display screen
screen = create_cube(0.6, (0, 0.9, 0.1), (1, 0.3, 0.02), material_black)
screen.name = 'Display Screen'

# Button positions for the calculator
button_coordinates = [(-0.6, 0.3), (-0.2, 0.3), (0.2, 0.3), (0.6, 0.3), (-0.6, 0), (-0.2, 0), (0.2, 0), (0.6, 0), (-0.6, -0.3), (-0.2, -0.3), (0.2, -0.3), (0.6, -0.3), (-0.6, -0.6), (-0.2, -0.6), (0.2, -0.6), (0.6, -0.6), (-0.6, -0.9), (-0.2, -0.9), (0.2, -0.9), (0.6, -0.9)]

for index, (pos_x, pos_y) in enumerate(button_coordinates):
    button = create_cube(0.2, (pos_x, pos_y, 0.1), (0.3, 0.3, 0.05), material_black)
    button.name = f'Button {index + 1}'

# Create the clear key
clear_btn = create_cube(0.2, (0.6, 0.6, 0.1), (0.3, 0.3, 0.05), material_black)
clear_btn.name = 'Clear Key'


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
