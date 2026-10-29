# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_drum_using_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build drum using blender code

import bpy
import math

# Clear the entire scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the drum components
body_material = bpy.data.materials.new(name='Body Material')
body_material.diffuse_color = (0.5, 0.2, 0.1, 1)
drumhead_material = bpy.data.materials.new(name='Drumhead Material')
drumhead_material.diffuse_color = (0.9, 0.9, 0.9, 1)
tension_rod_material = bpy.data.materials.new(name='Rod Material')
tension_rod_material.diffuse_color = (0.8, 0.8, 0.8, 1)
drumstick_material = bpy.data.materials.new(name='Stick Material')
drumstick_material.diffuse_color = (0.7, 0.4, 0.1, 1)

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the drum body
create_cylinder(1, 1.5, (0, 0, 0.75), 'Drum Body', body_material)

# Create the drumhead
create_cylinder(1.05, 0.05, (0, 0, 1.525), 'Drumhead', drumhead_material)

# Create tension rods
num_rods = 8
for i in range(num_rods):
    angle = 2 * math.pi * i / num_rods
    x = 1.1 * math.cos(angle)
    y = 1.1 * math.sin(angle)
    create_cylinder(0.03, 1.6, (x, y, 0.8), f'Tension Rod {i + 1}', tension_rod_material)

# Create drumsticks
create_cylinder(0.05, 1, (1.5, 0, 0.5), 'Drumstick 1', drumstick_material)
create_cylinder(0.05, 1, (1.5, 0.2, 0.5), 'Drumstick 2', drumstick_material)


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
