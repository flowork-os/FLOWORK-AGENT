# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_make_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to make a model of sofa

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for sofa and cushions
sofa_material = bpy.data.materials.new(name="Sofa")
sofa_material.diffuse_color = (0.5, 0.25, 0.25, 1)

cushion_material = bpy.data.materials.new(name="Cushions")
cushion_material.diffuse_color = (0.8, 0.8, 0.8, 1)

# Class for Sofa
class Sofa:
    def __init__(self):
        self.create_sofa_base()
        self.create_backrest()
        self.create_seat_cushions()
        self.create_backrest_cushions()

    def create_sofa_base(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
        base = bpy.context.object
        base.scale = (2, 1, 0.5)
        base.name = "SofaBase"
        base.data.materials.append(sofa_material)

    def create_backrest(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, -0.75, 1.25))
        backrest = bpy.context.object
        backrest.scale = (2, 0.25, 0.75)
        backrest.name = "Backrest"
        backrest.data.materials.append(sofa_material)

    def create_seat_cushions(self):
        for i in range(3):
            bpy.ops.mesh.primitive_cube_add(size=2, location=(-1.25 + i * 1.25, 0, 1))
            cushion = bpy.context.object
            cushion.scale = (0.6, 0.9, 0.2)
            cushion.name = f"SeatCushion_{i + 1}"
            cushion.data.materials.append(cushion_material)

    def create_backrest_cushions(self):
        for i in range(3):
            bpy.ops.mesh.primitive_cube_add(size=2, location=(-1.25 + i * 1.25, -0.75, 1.75))
            cushion = bpy.context.object
            cushion.scale = (0.6, 0.2, 0.5)
            cushion.name = f"BackrestCushion_{i + 1}"
            cushion.data.materials.append(cushion_material)

# Create the sofa
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
