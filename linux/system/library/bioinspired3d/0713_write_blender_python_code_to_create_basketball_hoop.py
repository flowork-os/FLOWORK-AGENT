# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_python_code_to_create_basketball_hoop" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender python code to create basketball hoop.

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with descriptive names
wood_material = bpy.data.materials.new(name="Wood")
wood_material.diffuse_color = (0.26, 0.14, 0.09, 1)
leaf_material = bpy.data.materials.new(name="Leaf")
leaf_material.diffuse_color = (0.13, 0.26, 0.13, 1)

# Function to create a leg

def create_leg(x, y, z):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.9, location=(x, y, z))
    leg = bpy.context.object
    leg.data.materials.append(wood_material)

# Generate the legs
for idx in range(4):
    pos_x = 0.7 * (idx % 2) - 0.35
    pos_y = 0.7 * (idx // 2) - 0.35
    create_leg(pos_x, pos_y, -0.45)

# Create the seat
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.1, location=(0, 0, 0))
seat_object = bpy.context.object
seat_object.data.materials.append(leaf_material)

# Create the backrest
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.1, location=(0, -0.3, 0.3), rotation=(math.pi / 2, 0, 0))
backrest_object = bpy.context.object
backrest_object.data.materials.append(wood_material)

# Function to create an arm

def create_arm(x, z, rotation):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.6, location=(x, 0, z), rotation=rotation)
    arm_object = bpy.context.object
    arm_object.data.materials.append(wood_material)

# Create arms
for index in range(2):
    arm_x = 0.45 * (index * 2 - 1)
    create_arm(arm_x, 0.3, (math.pi / 2, 0, 0))
for index in range(2):
    arm_x = 0.45 * (index * 2 - 1)
    create_arm(arm_x, 0.15, (0, 0, math.pi / 2))


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
