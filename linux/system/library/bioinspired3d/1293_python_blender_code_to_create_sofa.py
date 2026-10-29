# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_create_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to create sofa.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a material for the sofa
material_for_sofa = bpy.data.materials.new(name='SofaMaterial')
material_for_sofa.diffuse_color = (0.4, 0.3, 0.3, 1)  # Adjusted color

# Create a class to represent the sofa
class Sofa:
    def __init__(self):
        self.create_seat()
        self.create_backrest()
        self.create_armrests()

    def create_seat(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
        seat = bpy.context.object
        seat.name = 'Seat'
        seat.scale = (2, 1, 0.2)
        seat.data.materials.append(material_for_sofa)

    def create_backrest(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, -0.9, 1.2))
        backrest = bpy.context.object
        backrest.name = 'Backrest'
        backrest.scale = (2, 0.2, 1)
        backrest.data.materials.append(material_for_sofa)

    def create_armrests(self):
        for i in range(2):
            x_position = 2 * (i * 2 - 1)
            bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, 0.9))
            armrest = bpy.context.object
            armrest.name = f'Armrest_{i + 1}'
            armrest.scale = (0.2, 1, 0.7)
            armrest.data.materials.append(material_for_sofa)

# Instantiate the Sofa class
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
