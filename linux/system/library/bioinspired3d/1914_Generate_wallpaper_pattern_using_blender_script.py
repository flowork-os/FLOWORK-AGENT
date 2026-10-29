# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_wallpaper_pattern_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate wallpaper pattern using blender script

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material with a red hue
circle_mat = bpy.data.materials.new(name='Circle Material')
circle_mat.diffuse_color = (1, 0, 0, 1)  # RGB for red

# Class to handle circle creation
class CircleCreator:
    def __init__(self, material):
        self.material = material

    def create_circle(self, x, y):
        bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.1, location=(x, y, 0))
        circle = bpy.context.object
        circle.name = f'Circle_{x}_{y}'
        circle.data.materials.append(self.material)

# Instantiate the CircleCreator
creator = CircleCreator(circle_mat)

# Create the grid of circles
for i in range(5):
    for j in range(5):
        creator.create_circle(i, j)


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
