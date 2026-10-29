# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_builds_laptop" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that builds laptop

import bpy

# Clear the existing mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
material_black = bpy.data.materials.new(name="Material_Black")
material_black.diffuse_color = (0.0, 0.0, 0.0, 1)
material_gray = bpy.data.materials.new(name="Material_Gray")
material_gray.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to create a cube with specified parameters
def create_cube(size, location, scale, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.scale = scale
    cube.name = name
    cube.data.materials.append(material)
    return cube

# Create the components of the model
base = create_cube(2, (0, 0, 0.1), (1.5, 1, 0.05), "Base", material_gray)
screen = create_cube(2, (0, 0.9, 1.2), (1.5, 0.05, 1), "Screen", material_black)
keyboard = create_cube(2, (0, 0, 0.15), (1.4, 0.5, 0.02), "Keyboard", material_black)
touchpad = create_cube(2, (0, -0.5, 0.15), (0.4, 0.3, 0.01), "Touchpad", material_black)

# Create function keys
for i in range(12):
    x_position = -1.3 + i * 0.25
    create_cube(2, (x_position, 0.55, 0.17), (0.1, 0.05, 0.01), f"Function_Key_{i + 1}", material_black)

# Create ports on both sides
for i in range(3):
    create_cube(2, (-1.55, -0.9 + i * 0.3, 0.1), (0.05, 0.05, 0.02), f"Port_Left_{i + 1}", material_black)
    create_cube(2, (1.55, -0.9 + i * 0.3, 0.1), (0.05, 0.05, 0.02), f"Port_Right_{i + 1}", material_black)


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
