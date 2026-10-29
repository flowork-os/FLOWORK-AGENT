# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_python_blender_code_that_creates_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate python blender code that creates a model of sofa.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize a sofa color material
sofa_col = bpy.data.materials.new(name='SofaCol')
sofa_col.diffuse_color = (0.5, 0.3, 0.2, 1)  # Rich brown shade

# Function to create a sofa part

def create_sofa_part(part_name, loc, scl):
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc)
    part = bpy.context.object
    part.name = part_name
    part.scale = scl
    part.data.materials.append(sofa_col)

# Build the sofa components
create_sofa_part('Base', (0, 0, 0.5), (3, 1, 0.5))
create_sofa_part('Backrest', (0, -1, 1.5), (3, 0.2, 1))

# Add armrests
for j in range(2):
    arm_x = 3 * (j * 2 - 1)
    create_sofa_part(f'Armrest_{j + 1}', (arm_x, 0, 1), (0.2, 1, 1))

# Add seats
for j in range(3):
    seat_x = 2 * (j - 1)
    create_sofa_part(f'Seat_{j + 1}', (seat_x, 0, 1), (0.9, 1, 0.2))


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
