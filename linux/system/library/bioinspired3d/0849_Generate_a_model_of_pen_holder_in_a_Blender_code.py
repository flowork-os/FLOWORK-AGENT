# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_pen_holder_in_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of pen holder in a Blender code

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a gray material
mat_gray = bpy.data.materials.new(name="GrayMat")
mat_gray.diffuse_color = (0.5, 0.5, 0.5, 1)

# Class to handle cylinder creation
class CylinderCreator:
    @staticmethod
    def create(radius, depth, location, name):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        obj = bpy.context.object
        obj.name = name
        obj.data.materials.append(mat_gray)
        return obj

# Instantiate the cylinder creator
cylinder_creator = CylinderCreator()

# Create the base
cylinder_creator.create(1.5, 0.1, (0, 0, 0), "Base")

# Create the main compartment
cylinder_creator.create(1, 2, (0, 0, 1.05), "MainCompartment")

# Smaller compartments' locations
locs = [(1, 1, 0.8), (-1, 1, 0.8), (1, -1, 0.8), (-1, -1, 0.8)]
for idx, loc in enumerate(locs, start=1):
    cylinder_creator.create(0.5, 1.5, loc, f"Compartment_{idx}")


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
