# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_decorative_wall_panel_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of decorative wall panel using code in Blender

import bpy

# Step 1: Clear the Scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the panel and pattern
light_gray = bpy.data.materials.new(name="Light Gray")
light_gray.diffuse_color = (0.8, 0.8, 0.8, 1)
dark_gray = bpy.data.materials.new(name="Dark Gray")
dark_gray.diffuse_color = (0.2, 0.2, 0.2, 1)

# Step 2: Create the main panel
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
main_panel = bpy.context.object
main_panel.name = "MainPanel"
main_panel.data.materials.append(light_gray)

# Step 3: Generate the cube pattern
# Loop to create a grid of cubes
for x in range(-4, 5):
    for y in range(-4, 5):
        bpy.ops.mesh.primitive_cube_add(size=0.1, location=(x * 0.2, y * 0.2, 0.01))
        cube = bpy.context.object
        cube.name = f"Cube_{x}_{y}"
        cube.data.materials.append(dark_gray)


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
