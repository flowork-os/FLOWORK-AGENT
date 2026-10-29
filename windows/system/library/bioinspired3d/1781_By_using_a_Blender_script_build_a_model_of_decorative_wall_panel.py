# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_script_build_a_model_of_decorative_wall_panel" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender script build a model of decorative wall panel.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the panel and pattern
panel_material = bpy.data.materials.new(name="PanelMaterial")
panel_material.diffuse_color = (0.8, 0.8, 0.8, 1)
pattern_material = bpy.data.materials.new(name="PatternMaterial")
pattern_material.diffuse_color = (0.2, 0.2, 0.2, 1)

# Function to create a cube at a specific location
def create_cube(x, y):
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(x, y, 0.01))
    cube = bpy.context.object
    cube.data.materials.append(pattern_material)

# Create the main panel
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
panel = bpy.context.object
panel.name = "PanelObject"
panel.data.materials.append(panel_material)

# Create the grid of cubes using the helper function
for i in range(-4, 5):
    for j in range(-4, 5):
        create_cube(i * 0.2, j * 0.2)


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
