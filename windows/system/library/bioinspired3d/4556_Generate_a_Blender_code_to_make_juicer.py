# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_code_to_make_juicer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender code to make juicer.

import bpy
import math

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for various parts of the model
material_dark = bpy.data.materials.new(name="Dark Material")
material_dark.diffuse_color = (0.2, 0.2, 0.2, 1)
material_light = bpy.data.materials.new(name="Light Material")
material_light.diffuse_color = (0.8, 0.8, 0.8, 1)
material_medium = bpy.data.materials.new(name="Medium Material")
material_medium.diffuse_color = (0.5, 0.5, 0.5, 1)

# Define a function to add a cylinder with a specific name and color
def add_cylinder(radius, height, position, obj_name, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    obj = bpy.context.object
    obj.name = obj_name
    obj.data.materials.append(mat)

# Create all necessary parts of the model
add_cylinder(1, 0.5, (0, 0, 0.25), "Base", material_dark)
add_cylinder(0.9, 1.2, (0, 0, 1.1), "Juice Container", material_light)
add_cylinder(0.2, 0.8, (0, 0, 1.7), "Feeding Tube", material_light)
add_cylinder(0.1, 0.4, (0.9, 0, 0.9), "Spout", material_medium)
add_cylinder(0.5, 0.6, (-1.2, 0, 0.3), "Pulp Container", material_light)


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
