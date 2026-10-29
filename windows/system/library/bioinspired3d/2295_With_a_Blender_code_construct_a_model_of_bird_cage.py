# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_code_construct_a_model_of_bird_cage" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender code construct a model of bird cage.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

metal_material = bpy.data.materials.new(name="Metallic")
metal_material.diffuse_color = (0.6, 0.6, 0.6, 1)  # Lighter gray

def add_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(metal_material)
    return obj

base_cylinder = add_cylinder(1, 0.1, (0, 0, 0), "Cage_Base")
top_cylinder = add_cylinder(1, 0.1, (0, 0, 2), "Cage_Top")

num_of_bars = 16
for index in range(num_of_bars):
    angle_rad = (2 * math.pi / num_of_bars) * index
    x_pos = math.cos(angle_rad)
    y_pos = math.sin(angle_rad)
    add_cylinder(0.05, 2, (x_pos, y_pos, 1), f"Cage_Bar_{index + 1}")

bpy.ops.mesh.primitive_cube_add(size=0.5, location=(1, 0, 1))
door_cube = bpy.context.object
door_cube.name = "Cage_Door"
door_cube.data.materials.append(metal_material)

add_cylinder(0.05, 1.5, (0, 0, 0.5), "Cage_Perch")


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
