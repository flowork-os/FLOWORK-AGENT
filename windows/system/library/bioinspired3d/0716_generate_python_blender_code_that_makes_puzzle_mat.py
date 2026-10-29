# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_python_blender_code_that_makes_puzzle_mat" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate python blender code that makes puzzle mat.

import bpy
import math

# Removing all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
material_dark_wood = bpy.data.materials.new(name='DarkWood')
material_dark_wood.diffuse_color = (0.26, 0.14, 0.09, 1)
material_forest_green = bpy.data.materials.new(name='ForestGreen')
material_forest_green.diffuse_color = (0.13, 0.26, 0.13, 1)

# Create legs using a loop
for leg_index in range(4):
    leg_x = 0.7 * (leg_index % 2) - 0.35
    leg_y = 0.7 * (leg_index // 2) - 0.35
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.9, location=(leg_x, leg_y, -0.45))
    leg_object = bpy.context.object
    leg_object.name = f'Leg_{leg_index + 1}'
    leg_object.data.materials.append(material_dark_wood)

# Construct the seat
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.1, location=(0, 0, 0))
seat_object = bpy.context.object
seat_object.name = 'Chair_Seat'
seat_object.data.materials.append(material_forest_green)

# Create the backrest
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.1, location=(0, -0.3, 0.3), rotation=(math.pi / 2, 0, 0))
backrest_object = bpy.context.object
backrest_object.name = 'Chair_Backrest'
backrest_object.data.materials.append(material_dark_wood)

# Create arms
for arm_index in range(2):
    arm_x = 0.45 * (arm_index * 2 - 1)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.6, location=(arm_x, 0, 0.3), rotation=(math.pi / 2, 0, 0))
    arm_object = bpy.context.object
    arm_object.name = f'Arm_{arm_index + 1}'
    arm_object.data.materials.append(material_dark_wood)

for arm_index in range(2):
    arm_x = 0.45 * (arm_index * 2 - 1)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.3, location=(arm_x, 0, 0.15), rotation=(0, 0, math.pi / 2))
    arm_object = bpy.context.object
    arm_object.name = f'Arm_{arm_index + 3}'
    arm_object.data.materials.append(material_dark_wood)


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
