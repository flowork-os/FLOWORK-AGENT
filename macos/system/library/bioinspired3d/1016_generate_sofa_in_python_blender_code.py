# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_sofa_in_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate sofa in python blender code

import bpy

# Start fresh by removing all existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize a material for the sofa
material_sofa = bpy.data.materials.new(name="Material Sofa")
material_sofa.diffuse_color = (0.5, 0.25, 0.25, 1)  # Medium brown

# Create the sofa components using a class
class Sofa:
    def __init__(self):
        self.create_seat()
        self.create_backrest()
        self.create_armrests()

    def create_seat(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
        seat = bpy.context.object
        seat.name = "Seat"
        seat.scale = (2, 1, 0.2)
        seat.data.materials.append(material_sofa)

    def create_backrest(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, -1.1, 1.2))
        backrest = bpy.context.object
        backrest.name = "Backrest"
        backrest.scale = (2, 0.2, 0.8)
        backrest.data.materials.append(material_sofa)

    def create_armrests(self):
        for i in range(2):
            x_pos = 2 * (i * 2 - 1)
            bpy.ops.mesh.primitive_cube_add(size=2, location=(x_pos, 0, 0.9))
            armrest = bpy.context.object
            armrest.name = f"Armrest {i + 1}"
            armrest.scale = (0.2, 1, 0.6)
            armrest.data.materials.append(material_sofa)

# Instantiate the Sofa class to create the sofa
Sofa()


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
