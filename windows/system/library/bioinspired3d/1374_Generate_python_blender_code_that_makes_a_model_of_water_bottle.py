# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_python_blender_code_that_makes_a_model_of_water_bottle" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate python blender code that makes a model of water bottle.

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the bottle and its cap
bottle_color = bpy.data.materials.new(name='BottleColor')
bottle_color.diffuse_color = (0.2, 0.5, 0.8, 1)
cap_color = bpy.data.materials.new(name='CapColor')
cap_color.diffuse_color = (0.1, 0.1, 0.1, 1)

# Create the bottle and cap using a class
class Bottle:
    def __init__(self):
        self.body = self.create_part(0.3, 1.5, (0, 0, 0.75), 'BottleBody', bottle_color)
        self.neck = self.create_part(0.2, 0.3, (0, 0, 1.65), 'BottleNeck', bottle_color)
        self.cap = self.create_part(0.22, 0.2, (0, 0, 1.85), 'Cap', cap_color)

    def create_part(self, radius, depth, location, name, material):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        part = bpy.context.object
        part.name = name
        part.data.materials.append(material)
        return part

# Instantiate the Bottle class
bottle = Bottle()


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
