# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_for_constructing_a_model_of_chair_vs__stool" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script for constructing a model of chair vs. stool.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

wood_material = bpy.data.materials.new(name='Wooden Finish')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

def create_chair_legs():
    for index in range(4):
        x_position = 0.7 * (index % 2) - 0.35
        y_position = 0.7 * (index // 2) - 0.35
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.9, location=(x_position, y_position, -0.45))
        leg = bpy.context.object
        leg.name = f'Chair Leg {index + 1}'
        leg.data.materials.append(wood_material)

def create_chair_seat():
    bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.1, location=(0, 0, 0))
    seat = bpy.context.object
    seat.name = 'Chair Seat'
    seat.data.materials.append(wood_material)

def create_chair_backrest():
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0, -0.5, 0.45))
    backrest = bpy.context.object
    backrest.scale = (0.5, 0.05, 0.45)
    backrest.name = 'Chair Backrest'
    backrest.data.materials.append(wood_material)

create_chair_legs()
create_chair_seat()
create_chair_backrest()

def create_stool():
    for index in range(3):
        leg_angle = index * (2 * math.pi / 3)
        x_position = 0.35 * math.cos(leg_angle) + 2
        y_position = 0.35 * math.sin(leg_angle)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.9, location=(x_position, y_position, -0.45))
        leg = bpy.context.object
        leg.name = f'Stool Leg {index + 1}'
        leg.data.materials.append(wood_material)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.1, location=(2, 0, 0))
    stool_seat = bpy.context.object
    stool_seat.name = 'Stool Seat'
    stool_seat.data.materials.append(wood_material)

create_stool()


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
