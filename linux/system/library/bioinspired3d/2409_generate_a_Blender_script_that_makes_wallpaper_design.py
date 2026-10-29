# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_Blender_script_that_makes_wallpaper_design" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a Blender script that makes wallpaper design.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials with distinct colors
mat_red = bpy.data.materials.new(name='MatRed')
mat_red.diffuse_color = (0.8, 0.2, 0.2, 1)
mat_blue = bpy.data.materials.new(name='MatBlue')
mat_blue.diffuse_color = (0.2, 0.2, 0.8, 1)

# Create the initial torus
bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.3, location=(0, 0, 0))
torus = bpy.context.object
torus.name = 'Torus'
torus.data.materials.append(mat_red)

# Function to create a grid of toruses
def create_torus_grid(rows, cols):
    for row in range(rows):
        for col in range(cols):
            if row == 0 and col == 0:
                continue  # Skip the first torus
            bpy.ops.object.duplicate()
            new_torus = bpy.context.object
            new_torus.location = (row * 2, col * 2, 0)
            new_torus.data.materials[0] = mat_red if (row + col) % 2 == 0 else mat_blue

# Create a 3x3 grid of toruses
create_torus_grid(3, 3)


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
