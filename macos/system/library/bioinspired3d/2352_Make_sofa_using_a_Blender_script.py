# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_sofa_using_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make sofa using a Blender script

import bpy

# Clear all mesh objects in the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

class Sofa:
    def __init__(self):
        self.material = bpy.data.materials.new(name="Couch Material")
        self.material.diffuse_color = (0.4, 0.4, 0.4, 1)  # Darker gray

    def add_cube(self, size, location, scale, name):
        bpy.ops.mesh.primitive_cube_add(size=size, location=location)
        obj = bpy.context.object
        obj.name = name
        obj.scale = scale
        obj.data.materials.append(self.material)

# Instantiate the Sofa class
sofa = Sofa()

# Create the sofa components
sofa.add_cube(2, (0, 0, 0.5), (2, 1, 0.3), "Base")
sofa.add_cube(2, (0, -0.9, 1.15), (2, 0.2, 0.7), "Backrest")

# Create armrests
for i in range(2):
    armrest_position = 1.9 * (i * 2 - 1)
    sofa.add_cube(2, (armrest_position, 0, 0.85), (0.2, 1, 0.5), f"Armrest {i + 1}")


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
