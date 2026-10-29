# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_code__make_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender code, make a model of sofa.

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for sofa and cushions
sofa_material = bpy.data.materials.new(name='Sofa Material')
sofa_material.diffuse_color = (0.5, 0.3, 0.2, 1)
cushion_material = bpy.data.materials.new(name='Cushion Material')
cushion_material.diffuse_color = (0.8, 0.7, 0.6, 1)

# Function to create a cube with given parameters

def create_cube(size, location, scale, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    obj = bpy.context.object
    obj.scale = scale
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Construct the sofa base
sofa_base = create_cube(2, (0, 0, 0.5), (3, 1, 0.5), 'Sofa Base', sofa_material)

# Construct the backrest
backrest = create_cube(2, (0, -1, 1.25), (3, 0.2, 0.75), 'Backrest', sofa_material)

# Create armrests
for index in range(2):
    position_x = 3 * (index * 2 - 1)
    create_cube(2, (position_x, 0, 0.75), (0.2, 1, 0.75), f'Armrest {index + 1}', sofa_material)

# Create cushions
for index in range(3):
    cushion_x = (index - 1) * 2
    create_cube(2, (cushion_x, 0, 1.1), (0.9, 0.9, 0.2), f'Cushion Seat {index + 1}', cushion_material)
    create_cube(2, (cushion_x, -0.9, 1.7), (0.9, 0.2, 0.5), f'Cushion Back {index + 1}', cushion_material)

# Create legs
for index in range(4):
    leg_x = 2.8 * (index % 2) - 1.4
    leg_y = 0.8 * (index // 2) - 0.4
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.4, location=(leg_x, leg_y, 0.2))
    leg = bpy.context.object
    leg.name = f'Leg {index + 1}'
    leg.data.materials.append(sofa_material)


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
