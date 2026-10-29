# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_sofa_in_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build sofa in blender code

import bpy
import math

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the sofa
sofa_material = bpy.data.materials.new(name='SofaMaterial')
sofa_material.diffuse_color = (0.55, 0.25, 0.25, 1)  # Medium brown color

# Create seats using a function
def add_seat(i):
    x_pos = (i - 1) * 1.1
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_pos, 0, 0.5))
    seat = bpy.context.object
    seat.scale[1] = 1.5
    seat.scale[2] = 0.2
    seat.name = f'Seat_{i + 1}'
    seat.data.materials.append(sofa_material)

# Add seats
for i in range(3):
    add_seat(i)

# Create cushions using a function
def add_cushion(i):
    x_pos = (i - 1) * 1.1
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_pos, -0.75, 1))
    cushion = bpy.context.object
    cushion.scale[1] = 0.2
    cushion.scale[2] = 0.5
    cushion.name = f'Cushion_{i + 1}'
    cushion.data.materials.append(sofa_material)

# Add cushions
for i in range(3):
    add_cushion(i)

# Create armrests using a function
def add_armrest(i):
    x_pos = (i * 2 - 1) * 1.65
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_pos, 0, 0.75))
    armrest = bpy.context.object
    armrest.scale[0] = 0.1
    armrest.scale[1] = 1.5
    armrest.scale[2] = 0.5
    armrest.rotation_euler[1] = math.radians(15) if i == 0 else math.radians(-15)
    armrest.name = f'Armrest_{i + 1}'
    armrest.data.materials.append(sofa_material)

# Add armrests
for i in range(2):
    add_armrest(i)

# Create legs using a function
def add_leg(i):
    x_pos = (i % 2) * 2.2 - 1.1
    y_pos = (i // 2) * 1.5 - 0.75
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.5, location=(x_pos, y_pos, 0.25))
    leg = bpy.context.object
    leg.name = f'Leg_{i + 1}'
    leg.data.materials.append(sofa_material)

# Add legs
for i in range(4):
    add_leg(i)


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
