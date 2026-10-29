# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_script_that_creates_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender script that creates a model of sofa

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a material for the sofa
brown_material = bpy.data.materials.new(name="Brown Sofa")
brown_material.diffuse_color = (0.5, 0.25, 0.25, 1)  # Medium brown

# Create the sofa components using an object-oriented approach
class Sofa:
    def __init__(self):
        self.create_seat()
        self.create_backrest()
        self.create_armrests()

    def create_seat(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
        seat = bpy.context.object
        seat.scale = (2, 1, 0.2)
        seat.name = "Seat"
        seat.data.materials.append(brown_material)

    def create_backrest(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, -0.75, 1.1))
        backrest = bpy.context.object
        backrest.scale = (2, 0.1, 0.6)
        backrest.name = "Backrest"
        backrest.data.materials.append(brown_material)

    def create_armrests(self):
        for i in range(2):
            x_position = 1.9 * (i * 2 - 1)
            bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, 0.75))
            armrest = bpy.context.object
            armrest.scale = (0.1, 1, 0.4)
            armrest.name = f"Armrest {i + 1}"
            armrest.data.materials.append(brown_material)

# Instantiate the Sofa class to create the sofa
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
