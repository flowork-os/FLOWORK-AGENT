# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_that_makes_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code that makes sofa

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the sofa and cushions
sofa_mat = bpy.data.materials.new(name='Sofa Material')
sofa_mat.diffuse_color = (0.5, 0.3, 0.2, 1)
cushion_mat = bpy.data.materials.new(name='Cushion Material')
cushion_mat.diffuse_color = (0.8, 0.7, 0.6, 1)

# Function to add a cube to the scene

def add_cube(size, loc, scale, name, mat):
    bpy.ops.mesh.primitive_cube_add(size=size, location=loc)
    obj = bpy.context.object
    obj.scale = scale
    obj.name = name
    obj.data.materials.append(mat)

# Create the sofa's base
add_cube(2, (0, 0, 0.5), (3, 1, 0.5), 'Base', sofa_mat)

# Create the backrest
add_cube(2, (0, -1, 1.25), (3, 0.2, 0.75), 'Backrest', sofa_mat)

# Create the armrests
for i in range(2):
    add_cube(2, (3 * (i * 2 - 1), 0, 0.75), (0.2, 1, 0.75), f'Armrest {i + 1}', sofa_mat)

# Create cushions
for i in range(3):
    add_cube(2, ((i - 1) * 2, 0, 1.1), (0.9, 0.9, 0.2), f'Seat Cushion {i + 1}', cushion_mat)
    add_cube(2, ((i - 1) * 2, -0.9, 1.7), (0.9, 0.2, 0.5), f'Back Cushion {i + 1}', cushion_mat)

# Create legs
for i in range(4):
    leg_x = 2.8 * (i % 2) - 1.4
    leg_y = 0.8 * (i // 2) - 0.4
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.4, location=(leg_x, leg_y, 0.2))
    leg = bpy.context.object
    leg.name = f'Leg {i + 1}'
    leg.data.materials.append(sofa_mat)


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
