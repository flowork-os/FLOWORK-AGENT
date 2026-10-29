# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_code_that_creates_calculator" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender code that creates calculator.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with descriptive names
mat_body = bpy.data.materials.new(name='MainBodyMaterial')
mat_body.diffuse_color = (0.1, 0.1, 0.1, 1)
mat_button = bpy.data.materials.new(name='ControlButtonMaterial')
mat_button.diffuse_color = (0.8, 0.8, 0.8, 1)
mat_screen = bpy.data.materials.new(name='DisplayMaterial')
mat_screen.diffuse_color = (0.2, 0.8, 0.2, 1)

# Function to create a cube with specific properties
def create_cube(size, location, name, material, scale):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(material)
    return cube

# Construct the calculator body
body = create_cube(2, (0, 0, 0), 'CalculatorBody', mat_body, (1, 1.5, 0.1))

# Construct the LCD screen
screen = create_cube(1, (0, 1.2, 0.1), 'LCDScreen', mat_screen, (0.8, 0.3, 0.05))

# Button coordinates for the calculator
button_coords = [(-0.6, -0.6), (-0.2, -0.6), (0.2, -0.6), (0.6, -0.6),
                 (-0.6, -0.2), (-0.2, -0.2), (0.2, -0.2), (0.6, -0.2),
                 (-0.6, 0.2), (-0.2, 0.2), (0.2, 0.2), (0.6, 0.2),
                 (-0.6, 0.6), (-0.2, 0.6), (0.2, 0.6), (0.6, 0.6)]

# Create buttons using the defined coordinates
for index, (pos_x, pos_y) in enumerate(button_coords):
    button = create_cube(0.4, (pos_x, pos_y, 0.1), f'Button_{index + 1}', mat_button, (0.3, 0.3, 0.05))


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
