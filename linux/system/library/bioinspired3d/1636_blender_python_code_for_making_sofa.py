# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_making_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for making sofa.

import bpy

# Start by clearing the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a material for the sofa with a dark gray color
sofa_shader = bpy.data.materials.new(name="Sofa Shader")
sofa_shader.diffuse_color = (0.2, 0.2, 0.2, 1)  # Dark gray tone

# Class to represent a Sofa
class Sofa:
    def __init__(self):
        self.create_seat()
        self.create_backrest()
        self.create_armrests()

    def create_seat(self):
        self.add_cube("Seat", (0, 0, 0.5), (3, 1, 0.5))

    def create_backrest(self):
        self.add_cube("Backrest", (0, -1, 1.25), (3, 0.2, 1))

    def create_armrests(self):
        for i in range(2):
            x_pos = 3 * (i * 2 - 1)
            self.add_cube(f"Armrest {i + 1}", (x_pos, 0, 0.75), (0.2, 1, 0.75))

    def add_cube(self, name, loc, scale):
        bpy.ops.mesh.primitive_cube_add(size=2, location=loc)
        cube = bpy.context.object
        cube.name = name
        cube.scale = scale
        cube.data.materials.append(sofa_shader)

# Instantiate the Sofa class to build the model
sofa = Sofa()


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
