# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_sofa_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of sofa in a Blender script

import bpy
import math

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a new material for the sofa
brown_material = bpy.data.materials.new(name='BrownMaterial')
brown_material.diffuse_color = (0.6, 0.3, 0.3, 1)  # Light brown color

# Generate seats
for index in range(3):
    x_coord = (index - 1) * 1.1
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_coord, 0, 0.5))
    seat = bpy.context.object
    seat.scale[1] = 1.5
    seat.scale[2] = 0.2
    seat.name = f'Seat_{index + 1}'
    seat.data.materials.append(brown_material)

# Generate back cushions
for index in range(3):
    x_coord = (index - 1) * 1.1
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_coord, -0.75, 1))
    cushion = bpy.context.object
    cushion.scale[1] = 0.2
    cushion.scale[2] = 0.5
    cushion.name = f'Cushion_{index + 1}'
    cushion.data.materials.append(brown_material)

# Generate armrests
for index in range(2):
    x_coord = (index * 2 - 1) * 1.65
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_coord, 0, 0.75))
    arm = bpy.context.object
    arm.scale[0] = 0.1
    arm.scale[1] = 1.5
    arm.scale[2] = 0.5
    arm.rotation_euler[1] = math.radians(15) if index == 0 else math.radians(-15)
    arm.name = f'Armrest_{index + 1}'
    arm.data.materials.append(brown_material)

# Generate legs
for index in range(4):
    x_coord = (index % 2) * 2.2 - 1.1
    y_coord = (index // 2) * 1.5 - 0.75
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.5, location=(x_coord, y_coord, 0.25))
    leg = bpy.context.object
    leg.name = f'Leg_{index + 1}'
    leg.data.materials.append(brown_material)


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
