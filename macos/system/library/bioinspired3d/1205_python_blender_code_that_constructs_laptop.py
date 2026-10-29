# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_that_constructs_laptop" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code that constructs laptop.

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials
dark_material = bpy.data.materials.new(name="Dark_Material")
dark_material.diffuse_color = (0.0, 0.0, 0.0, 1)
light_material = bpy.data.materials.new(name="Light_Material")
light_material.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to add cubes with materials
def add_cube(size, position, scale_factors, obj_name, mat):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    cube_object = bpy.context.object
    cube_object.scale = scale_factors
    cube_object.name = obj_name
    cube_object.data.materials.append(mat)

# Adding the main components
add_cube(2, (0, 0, 0.1), (1.5, 1, 0.05), "Main_Base", light_material)
add_cube(2, (0, 0.9, 1.2), (1.5, 0.05, 1), "Display_Screen", dark_material)
add_cube(2, (0, 0, 0.15), (1.4, 0.5, 0.02), "Input_Keyboard", dark_material)
add_cube(2, (0, -0.5, 0.15), (0.4, 0.3, 0.01), "Control_Touchpad", dark_material)

# Generating function keys
for i in range(12):
    x_coord = -1.3 + i * 0.25
    add_cube(2, (x_coord, 0.55, 0.17), (0.1, 0.05, 0.01), f"FuncKey_{i + 1}", dark_material)

# Adding ports
for i in range(3):
    add_cube(2, (-1.55, -0.9 + i * 0.3, 0.1), (0.05, 0.05, 0.02), f"LeftPort_{i + 1}", dark_material)
    add_cube(2, (1.55, -0.9 + i * 0.3, 0.1), (0.05, 0.05, 0.02), f"RightPort_{i + 1}", dark_material)


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
