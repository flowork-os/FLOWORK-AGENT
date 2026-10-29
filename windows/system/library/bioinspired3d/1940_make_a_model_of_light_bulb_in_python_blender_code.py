# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_light_bulb_in_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of light bulb in python blender code

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Class to handle creating objects
class ObjectCreator:
    @staticmethod
    def create_sphere(name, radius, location, material):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location)
        obj = bpy.context.object
        obj.name = name
        obj.data.materials.append(material)
        return obj

    @staticmethod
    def create_cylinder(name, radius, depth, location, material):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        obj = bpy.context.object
        obj.name = name
        obj.data.materials.append(material)
        return obj

# Create materials
white_material = bpy.data.materials.new(name='WhiteMaterial')
white_material.diffuse_color = (1, 1, 1, 1)
gray_material = bpy.data.materials.new(name='GrayMaterial')
gray_material.diffuse_color = (0.5, 0.5, 0.5, 1)

# Generate the bulb and base
ObjectCreator.create_sphere('Bulb', 1, (0, 0, 1.5), white_material)
ObjectCreator.create_cylinder('Base', 0.5, 1, (0, 0, 0.5), gray_material)


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
