# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_makes_a_model_of_syringe_pump" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that makes a model of syringe pump

import bpy

# Clear all existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with specific colors
material_gray = bpy.data.materials.new(name="Material Gray")
material_gray.diffuse_color = (0.5, 0.5, 0.5, 1)
material_dark = bpy.data.materials.new(name="Material Dark")
material_dark.diffuse_color = (0.2, 0.2, 0.2, 1)
material_blueish = bpy.data.materials.new(name="Material Blueish")
material_blueish.diffuse_color = (0.1, 0.1, 0.8, 1)
material_greenish = bpy.data.materials.new(name="Material Greenish")
material_greenish.diffuse_color = (0.1, 0.8, 0.1, 1)

# Function to create and return a cube object
def create_cube_obj(size, loc, obj_name, scale_factors, mat):
    bpy.ops.mesh.primitive_cube_add(size=size, location=loc)
    cube = bpy.context.object
    cube.name = obj_name
    cube.scale = scale_factors
    cube.data.materials.append(mat)
    return cube

# Main body
create_cube_obj(2, (0, 0, 0), "Body", (1, 0.5, 0.3), material_gray)

# Syringe slot
create_cube_obj(1, (0, 0.6, 0), "Syringe Slot", (0.8, 0.1, 0.2), material_dark)

# Interface
create_cube_obj(1, (0, -0.6, 0.1), "Control Interface", (0.8, 0.1, 0.2), material_dark)

# Buttons
for index in range(3):
    create_cube_obj(0.1, (-0.3 + index * 0.3, -0.7, 0.1), f"Button {index + 1}", (0.1, 0.05, 0.05), material_blueish)

# Screen
create_cube_obj(0.4, (0.5, -0.7, 0.1), "Display", (0.3, 0.05, 0.1), material_greenish)


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
