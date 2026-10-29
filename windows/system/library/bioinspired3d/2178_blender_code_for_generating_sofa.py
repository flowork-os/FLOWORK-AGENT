# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_for_generating_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code for generating sofa.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a new material for the sofa
sofa_surface = bpy.data.materials.new(name='Sofa Surface')
sofa_surface.diffuse_color = (0.5, 0.25, 0.25, 1)

# Create sofa components using a functional approach
def add_sofa_part(part_name, part_location, part_scale):
    bpy.ops.mesh.primitive_cube_add(size=2, location=part_location)
    part = bpy.context.object
    part.name = part_name
    part.scale = part_scale
    part.data.materials.append(sofa_surface)

# Sofa base
add_sofa_part('Sofa Base', (0, 0, 0.5), (2, 1, 0.2))

# Backrest
add_sofa_part('Backrest', (0, -0.9, 1.1), (2, 0.2, 0.6))

# Armrests
for i in range(2):
    add_sofa_part(f'Armrest {i + 1}', (2 * (i * 2 - 1), 0, 0.75), (0.2, 1, 0.5))

# Cushions
for j in range(3):
    add_sofa_part(f'Cushion {j + 1}', ((j - 1) * 1.3, 0, 0.75), (0.6, 1, 0.2))


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
