# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_script_to_create_a_model_of_laptop" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender script to create a model of laptop.

import bpy

# Remove all mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a dark gray material
material_dark_gray = bpy.data.materials.new(name="Material Dark")
material_dark_gray.diffuse_color = (0.15, 0.15, 0.15, 1)

# Class to represent a 3D Component
class Component:
    def __init__(self, size, loc, scale, name):
        bpy.ops.mesh.primitive_cube_add(size=size, location=loc)
        self.object = bpy.context.object
        self.object.scale = scale
        self.object.name = name
        self.object.data.materials.append(material_dark_gray)

# Create the base
base_component = Component(2, (0, 0, 0.1), (1, 1, 0.05), "Base")

# Create the keyboard
keyboard_component = Component(1.8, (0, 0, 0.15), (1, 1, 0.01), "Keyboard")

# Create the screen
screen_component = Component(2, (0, 0.95, 1.05), (1, 1, 0.05), "Screen")
screen_component.object.rotation_euler[0] = 1.5708  # Set vertical orientation

# Generate ports
for i in range(3):
    Component(0.1, (-1, 0.9 - i * 0.3, 0.1), (1, 1, 0.02), f"Port {i + 1}")


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
