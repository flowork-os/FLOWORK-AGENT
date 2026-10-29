# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_generates_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that generates a model of sofa.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

sofa_material = bpy.data.materials.new(name='SofaMaterial')
sofa_material.diffuse_color = (0.4, 0.2, 0.2, 1)  # Darker brown shade

def create_seat(index):
    position_x = (index - 1) * 1.1
    bpy.ops.mesh.primitive_cube_add(size=1, location=(position_x, 0, 0.5))
    seat_object = bpy.context.object
    seat_object.scale[1] = 1.5
    seat_object.scale[2] = 0.2
    seat_object.name = f'Seat_{index + 1}'
    seat_object.data.materials.append(sofa_material)

for i in range(3):
    create_seat(i)

def create_cushion(index):
    position_x = (index - 1) * 1.1
    bpy.ops.mesh.primitive_cube_add(size=1, location=(position_x, -0.75, 1))
    cushion_object = bpy.context.object
    cushion_object.scale[1] = 0.2
    cushion_object.scale[2] = 0.5
    cushion_object.name = f'Cushion_{index + 1}'
    cushion_object.data.materials.append(sofa_material)

for i in range(3):
    create_cushion(i)

def create_armrest(index):
    position_x = (index * 2 - 1) * 1.65
    bpy.ops.mesh.primitive_cube_add(size=1, location=(position_x, 0, 0.75))
    armrest_object = bpy.context.object
    armrest_object.scale[0] = 0.1
    armrest_object.scale[1] = 1.5
    armrest_object.scale[2] = 0.5
    armrest_object.rotation_euler[1] = math.radians(15) if index == 0 else math.radians(-15)
    armrest_object.name = f'Armrest_{index + 1}'
    armrest_object.data.materials.append(sofa_material)

for i in range(2):
    create_armrest(i)

def create_leg(index):
    position_x = (index % 2) * 2.2 - 1.1
    position_y = (index // 2) * 1.5 - 0.75
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.5, location=(position_x, position_y, 0.25))
    leg_object = bpy.context.object
    leg_object.name = f'Leg_{index + 1}'
    leg_object.data.materials.append(sofa_material)

for i in range(4):
    create_leg(i)


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
