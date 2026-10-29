# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_script_that_makes_syringe_pump" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender script that makes syringe pump

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials with different names
mat_light_gray = bpy.data.materials.new(name="Material Light Gray")
mat_light_gray.diffuse_color = (0.5, 0.5, 0.5, 1)
mat_dark_gray = bpy.data.materials.new(name="Material Dark Gray")
mat_dark_gray.diffuse_color = (0.2, 0.2, 0.2, 1)
mat_blue = bpy.data.materials.new(name="Material Blue")
mat_blue.diffuse_color = (0.1, 0.1, 0.8, 1)
mat_green = bpy.data.materials.new(name="Material Green")
mat_green.diffuse_color = (0.1, 0.8, 0.1, 1)

# Function to set up a cube with material
def add_cube(size, position, identifier, scale_factor, mat):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    cube_object = bpy.context.object
    cube_object.name = identifier
    cube_object.scale = scale_factor
    cube_object.data.materials.append(mat)

# Main body creation
add_cube(2, (0, 0, 0), "Base", (1, 0.5, 0.3), mat_light_gray)

# Syringe slot
add_cube(1, (0, 0.6, 0), "Syringe Slot", (0.8, 0.1, 0.2), mat_dark_gray)

# Interface creation
add_cube(1, (0, -0.6, 0.1), "Interface", (0.8, 0.1, 0.2), mat_dark_gray)

# Button creation loop
for j in range(3):
    add_cube(0.1, (-0.3 + j * 0.3, -0.7, 0.1), f"Button {j + 1}", (0.1, 0.05, 0.05), mat_blue)

# Screen creation
add_cube(0.4, (0.5, -0.7, 0.1), "Screen", (0.3, 0.05, 0.1), mat_green)


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
