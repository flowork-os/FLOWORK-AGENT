# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_creates_dish_rack" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that creates dish rack

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize a gray material for the model
mat_gray = bpy.data.materials.new(name="GrayMaterial")
mat_gray.diffuse_color = (0.5, 0.5, 0.5, 1)

# Class to represent a geometric object
class GeometricObject:
    def __init__(self, size, location, name, scale, material):
        bpy.ops.mesh.primitive_cube_add(size=size, location=location)
        self.object = bpy.context.object
        self.object.name = name
        self.object.scale = scale
        self.object.data.materials.append(material)

# Create the base object
base_object = GeometricObject(2, (0, 0, 0.1), "BaseObject", (1, 0.5, 0.05), mat_gray)

# Create slots for plates
for index in range(5):
    x_slot = -0.9 + index * 0.4
    GeometricObject(1, (x_slot, 0, 0.35), f"Slot{index + 1}", (0.1, 0.05, 0.5), mat_gray)

# Create the area for cups and utensils
GeometricObject(1, (0, -0.35, 0.1), "CupArea", (0.9, 0.4, 0.05), mat_gray)


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
