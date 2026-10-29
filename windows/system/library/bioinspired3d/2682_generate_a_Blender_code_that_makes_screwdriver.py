# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_Blender_code_that_makes_screwdriver" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a Blender code that makes screwdriver.

import bpy

# Start with a clean slate by removing all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with distinct names and colors
metal_material = bpy.data.materials.new(name="Steel")
metal_material.diffuse_color = (0.7, 0.7, 0.7, 1)  # Steel color
handle_material = bpy.data.materials.new(name="Crimson")
handle_material.diffuse_color = (0.9, 0, 0, 1)  # Crimson red

# Define a class for creating 3D objects
class ObjectCreator:
    @staticmethod
    def add_cylinder(radius, depth, position, obj_name, mat):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
        obj = bpy.context.object
        obj.name = obj_name
        obj.data.materials.append(mat)

    @staticmethod
    def add_cube(size, position, obj_name, mat):
        bpy.ops.mesh.primitive_cube_add(size=size, location=position)
        obj = bpy.context.object
        obj.name = obj_name
        obj.data.materials.append(mat)

# Create the handle, shaft, and head
creator = ObjectCreator()
creator.add_cylinder(0.1, 1.0, (0, 0, 0.5), "Handle", handle_material)
creator.add_cylinder(0.02, 1.5, (0, 0, 1.75), "Shaft", metal_material)
creator.add_cube(0.1, (0, 0, 2.55), "Flat Head", metal_material)

# Flatten the head by adjusting its scale
head = bpy.context.object
head.scale[1] = 0.02


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
