# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_code__construct_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender code, construct sofa

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions
brown_material = bpy.data.materials.new(name='BrownSofa')
brown_material.diffuse_color = (0.5, 0.25, 0.1, 1)

light_gray_material = bpy.data.materials.new(name='LightGrayCushion')
light_gray_material.diffuse_color = (0.8, 0.8, 0.8, 1)

# Function to create a cube with specified parameters

def create_cube(name, size, location, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(material)
    return cube

# Create the seat
create_cube('SofaSeat', 2, (0, 0, 0.5), (2, 1, 0.2), brown_material)

# Create the backrest
create_cube('SofaBackrest', 2, (0, -0.9, 1.1), (2, 0.2, 0.6), brown_material)

# Create armrests
for side in [-1, 1]:
    create_cube(f'Armrest_{side + 2}', 2, (side * 1.9, 0, 0.8), (0.2, 1, 0.6), brown_material)

# Create legs
for index in range(4):
    leg_x = 1.8 * (index % 2) - 0.9
    leg_y = 0.8 * (index // 2) - 0.4
    create_cube(f'Leg_{index + 1}', 0.2, (leg_x, leg_y, 0.1), (0.1, 0.1, 0.1), brown_material)

# Create seat cushions
for cushion_index in range(3):
    cushion_x = 1.2 * (cushion_index - 1)
    create_cube(f'SeatCushion_{cushion_index + 1}', 1, (cushion_x, 0, 0.9), (0.6, 0.9, 0.2), light_gray_material)

# Create back cushions
for back_index in range(3):
    back_x = 1.2 * (back_index - 1)
    create_cube(f'BackCushion_{back_index + 1}', 1, (back_x, -0.9, 1.4), (0.6, 0.2, 0.4), light_gray_material)


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
