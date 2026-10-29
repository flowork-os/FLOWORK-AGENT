# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_power_line_in_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of power line in blender code

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a gray material
mat_gray = bpy.data.materials.new(name="GrayMaterial")
mat_gray.diffuse_color = (0.5, 0.5, 0.5, 1)

class Structure:
    def __init__(self):
        self.material = mat_gray

    def add_cylinder(self, radius, depth, location, rotation, name):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, rotation=rotation)
        obj = bpy.context.object
        obj.name = name
        obj.data.materials.append(self.material)

# Instantiate the structure
structure = Structure()

# Create the pole
structure.add_cylinder(0.1, 5, (0, 0, 2.5), (0, 0, 0), "Pole")

# Create the crossbar
structure.add_cylinder(0.05, 1.5, (0, 0, 4.5), (1.5708, 0, 0), "Crossbar")

# Create power lines
for i in range(3):
    y_coord = 0.5 * (i - 1)
    structure.add_cylinder(0.01, 5, (0, y_coord, 4.5), (0, 1.5708, 0), f"Line_{i + 1}")


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
