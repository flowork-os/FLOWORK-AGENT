# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_constructs_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that constructs a model of sofa.

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a light gray material
light_gray_material = bpy.data.materials.new(name='Light Gray')
light_gray_material.diffuse_color = (0.85, 0.85, 0.85, 1)

# Function for adding a cube
def add_cube(size, position, scale_factors, object_name, mat):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    cube_obj = bpy.context.object
    cube_obj.scale = scale_factors
    cube_obj.name = object_name
    cube_obj.data.materials.append(mat)

# Create chair components
add_cube(2, (0, 0, 0.5), (2, 1, 0.2), 'Chair Seat', light_gray_material)
add_cube(2, (0, -0.75, 1.2), (2, 0.2, 0.7), 'Backrest', light_gray_material)

# Generate armrests
for arm in range(2):
    x_position = 2 * (arm * 2 - 1)
    add_cube(2, (x_position, 0, 0.75), (0.2, 1, 0.5), f'Armrest_{arm + 1}', light_gray_material)


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
