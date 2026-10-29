# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_code_to_create_a_model_of_wallpaper_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender code to create a model of wallpaper pattern.

import bpy

# Clear the existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the shapes
material_gray = bpy.data.materials.new(name="Gray Material")
material_gray.diffuse_color = (0.5, 0.5, 0.5, 1)  # Set to medium gray

# Function to generate a cube at a specified location
def add_cube(x_pos, y_pos):
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(x_pos, y_pos, 0))
    cube = bpy.context.object
    cube.data.materials.append(material_gray)

# Construct the grid of cubes
num_rows = 5
num_columns = 5
cube_spacing = 1.0

for row in range(num_rows):
    for column in range(num_columns):
        add_cube(row * cube_spacing, column * cube_spacing)


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
