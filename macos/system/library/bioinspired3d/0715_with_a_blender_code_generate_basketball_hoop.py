# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_blender_code_generate_basketball_hoop" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a blender code generate basketball hoop

import bpy
import math

# Clear all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
mahogany_material = bpy.data.materials.new(name="Mahogany")
mahogany_material.diffuse_color = (0.26, 0.14, 0.09, 1)
forest_material = bpy.data.materials.new(name="Forest")
forest_material.diffuse_color = (0.13, 0.26, 0.13, 1)

# Helper function for creating a cylinder

def create_cylinder(radius, height, position, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position, rotation=rot)
    return bpy.context.object

# Create legs
for i in range(4):
    position_x = 0.7 * (i % 2) - 0.35
    position_y = 0.7 * (i // 2) - 0.35
    leg = create_cylinder(0.05, 0.9, (position_x, position_y, -0.45))
    leg.data.materials.append(mahogany_material)

# Construct the seat
seat_object = create_cylinder(0.5, 0.1, (0, 0, 0))
seat_object.data.materials.append(forest_material)

# Add the backrest
backrest_object = create_cylinder(0.5, 0.1, (0, -0.3, 0.3), rot=(math.pi / 2, 0, 0))
backrest_object.data.materials.append(mahogany_material)

# Create arms
for j in range(2):
    arm_x_position = 0.45 * (j * 2 - 1)
    create_cylinder(0.03, 0.6, (arm_x_position, 0, 0.3), rot=(math.pi / 2, 0, 0)).data.materials.append(mahogany_material)
    create_cylinder(0.03, 0.3, (arm_x_position, 0, 0.15), rot=(0, 0, math.pi / 2)).data.materials.append(mahogany_material)


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
