# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_for_creating_drum" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script for creating drum.

import bpy
import math

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the drum components
mat_body = bpy.data.materials.new(name='Body')
mat_body.diffuse_color = (0.5, 0.2, 0.1, 1)
mat_head = bpy.data.materials.new(name='Head')
mat_head.diffuse_color = (0.9, 0.9, 0.9, 1)
mat_rod = bpy.data.materials.new(name='Rod')
mat_rod.diffuse_color = (0.8, 0.8, 0.8, 1)
mat_stick = bpy.data.materials.new(name='Stick')
mat_stick.diffuse_color = (0.7, 0.4, 0.1, 1)

# Function to add a cylinder with specified parameters

def add_cylinder(radius, depth, position, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)

# Create drum body
add_cylinder(1, 1.5, (0, 0, 0.75), 'Drum Body', mat_body)

# Create drumhead
add_cylinder(1.05, 0.05, (0, 0, 1.525), 'Drumhead', mat_head)

# Create tension rods
for index in range(8):
    radian = 2 * math.pi * index / 8
    x_coord = 1.1 * math.cos(radian)
    y_coord = 1.1 * math.sin(radian)
    add_cylinder(0.03, 1.6, (x_coord, y_coord, 0.8), f'Tension Rod {index + 1}', mat_rod)

# Create drumsticks
add_cylinder(0.05, 1, (1.5, 0, 0.5), 'Drumstick 1', mat_stick)
add_cylinder(0.05, 1, (1.5, 0.2, 0.5), 'Drumstick 2', mat_stick)


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
