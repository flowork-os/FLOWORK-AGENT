# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_logo_in_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of logo in python blender code

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Setup gear material
gear_material = bpy.data.materials.new(name="Material for Gears")
gear_material.diffuse_color = (0.4, 0.4, 0.4, 1)  # Darker gray

# Class to represent a Gear
class Gear:
    def __init__(self, location, name):
        self.create_gear(location, name)

    def create_gear(self, location, name):
        bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.2, location=location)
        gear_object = bpy.context.object
        gear_object.name = name
        gear_object.data.materials.append(gear_material)

# Instantiate gears at different positions
Gear((0, 0, 0), "Gear 1")
Gear((1.5, 0, 0), "Gear 2")
Gear((0.75, 1.3, 0), "Gear 3")


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
