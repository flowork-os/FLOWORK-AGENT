# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_to_build_a_model_of_puzzle_mat" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender to build a model of puzzle mat

import bpy
import math

# Clear the mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials
mahogany_material = bpy.data.materials.new(name='MahoganyMaterial')
mahogany_material.diffuse_color = (0.26, 0.14, 0.09, 1)
forest_green_material = bpy.data.materials.new(name='ForestGreenMaterial')
forest_green_material.diffuse_color = (0.13, 0.26, 0.13, 1)

# Function to add a cylinder
def add_cylinder(radius, depth, location, rotation, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)

# Create legs
for i in range(4):
    leg_x = 0.7 * (i % 2) - 0.35
    leg_y = 0.7 * (i // 2) - 0.35
    add_cylinder(0.05, 0.9, (leg_x, leg_y, -0.45), (0, 0, 0), f'Leg_{i + 1}', mahogany_material)

# Create seat
add_cylinder(0.5, 0.1, (0, 0, 0), (0, 0, 0), 'Seat', forest_green_material)

# Create backrest
add_cylinder(0.5, 0.1, (0, -0.3, 0.3), (math.pi / 2, 0, 0), 'Backrest', mahogany_material)

# Create arms
for j in range(2):
    add_cylinder(0.03, 0.6, (0.45 * (j * 2 - 1), 0, 0.3), (math.pi / 2, 0, 0), f'Arm_{j + 1}', mahogany_material)
for j in range(2):
    add_cylinder(0.03, 0.3, (0.45 * (j * 2 - 1), 0, 0.15), (0, 0, math.pi / 2), f'Arm_{j + 3}', mahogany_material)


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
