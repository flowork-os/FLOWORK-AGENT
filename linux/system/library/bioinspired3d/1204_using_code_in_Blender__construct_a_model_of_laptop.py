# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_code_in_Blender__construct_a_model_of_laptop" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using code in Blender, construct a model of laptop

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the model components
mat_black = bpy.data.materials.new(name="Mat_Black")
mat_black.diffuse_color = (0.0, 0.0, 0.0, 1)
mat_gray = bpy.data.materials.new(name="Mat_Gray")
mat_gray.diffuse_color = (0.5, 0.5, 0.5, 1)

# Class to represent a 3D component
class Component:
    def __init__(self, size, location, scale, name, material):
        bpy.ops.mesh.primitive_cube_add(size=size, location=location)
        self.obj = bpy.context.object
        self.obj.scale = scale
        self.obj.name = name
        self.obj.data.materials.append(material)

# Create the model components
Component(2, (0, 0, 0.1), (1.5, 1, 0.05), "Base", mat_gray)
Component(2, (0, 0.9, 1.2), (1.5, 0.05, 1), "Screen", mat_black)
Component(2, (0, 0, 0.15), (1.4, 0.5, 0.02), "Keyboard", mat_black)
Component(2, (0, -0.5, 0.15), (0.4, 0.3, 0.01), "Touchpad", mat_black)

# Create function keys
for i in range(12):
    key_x = -1.3 + i * 0.25
    Component(2, (key_x, 0.55, 0.17), (0.1, 0.05, 0.01), f"Func_Key_{i + 1}", mat_black)

# Create ports on both sides
for i in range(3):
    Component(2, (-1.55, -0.9 + i * 0.3, 0.1), (0.05, 0.05, 0.02), f"Left_Port_{i + 1}", mat_black)
    Component(2, (1.55, -0.9 + i * 0.3, 0.1), (0.05, 0.05, 0.02), f"Right_Port_{i + 1}", mat_black)


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
