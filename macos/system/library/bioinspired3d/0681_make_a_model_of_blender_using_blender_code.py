# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_blender_using_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of blender using blender code

import bpy

# Start by clearing the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for different parts of the model
base_material = bpy.data.materials.new(name="Gray Base")
base_material.diffuse_color = (0.2, 0.2, 0.2, 1)
button_material = bpy.data.materials.new(name="Red Button")
button_material.diffuse_color = (0.8, 0.1, 0.1, 1)
jar_material = bpy.data.materials.new(name="Light Gray Jar")
jar_material.diffuse_color = (0.8, 0.8, 0.8, 0.3)
lid_material = bpy.data.materials.new(name="Black Lid")
lid_material.diffuse_color = (0.1, 0.1, 0.1, 1)

# Class to manage the creation of objects
class ObjectCreator:
    @staticmethod
    def create_cylinder(radius, depth, location, name, material):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        obj = bpy.context.object
        obj.name = name
        obj.data.materials.append(material)

# Create base, buttons, jar, and lid
ObjectCreator.create_cylinder(1, 0.5, (0, 0, 0.25), "Base", base_material)
for i in range(3):
    ObjectCreator.create_cylinder(0.1, 0.2, (0.4 * (i - 1), 0.9, 0.1), f"Button_{i + 1}", button_material)
ObjectCreator.create_cylinder(0.8, 1.5, (0, 0, 1.25), "Jar", jar_material)
ObjectCreator.create_cylinder(0.85, 0.1, (0, 0, 2), "Lid", lid_material)


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
