# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_python_code_make_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender python code make sofa.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the sofa
sofa_material = bpy.data.materials.new(name='SofaMaterial')
sofa_material.diffuse_color = (0.4, 0.2, 0.2, 1)  # Darker brown

# Function to create a cube with given parameters

def create_cube(name, location, scale):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(sofa_material)
    return cube

# Create the Seat
seat_scale = (2, 1, 0.2)
create_cube('Seat', (0, 0, 0.5), seat_scale)

# Create the Backrest
backrest_scale = (2, 0.2, 1)
create_cube('Backrest', (0, -1.1, 1.2), backrest_scale)

# Create the Armrests
for i in range(2):
    armrest_location = (2.1 * (i * 2 - 1), 0, 0.9)
    armrest_scale = (0.2, 1, 0.6)
    create_cube(f'Armrest {i + 1}', armrest_location, armrest_scale)

# Create the Legs
for i in range(4):
    leg_location = (1.8 * (i % 2) - 0.9, 0.8 * (i // 2) - 0.4, 0.1)
    leg_scale = (0.2, 0.2, 0.5)
    create_cube(f'Leg {i + 1}', leg_location, leg_scale)


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
