# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_Blender_script_to_create_wallpaper_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a Blender script to create wallpaper pattern

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the cube pattern
cube_material = bpy.data.materials.new(name='Cube Material')
cube_material.diffuse_color = (0.5, 0.5, 0.5, 1)  # Medium gray color

# Class to handle cube creation
class CubeGrid:
    def __init__(self, rows, cols, spacing):
        self.rows = rows
        self.cols = cols
        self.spacing = spacing

    def generate_cubes(self):
        for row in range(self.rows):
            for col in range(self.cols):
                self.create_cube(row * self.spacing, col * self.spacing)

    def create_cube(self, x, y):
        bpy.ops.mesh.primitive_cube_add(size=0.5, location=(x, y, 0))
        cube = bpy.context.object
        cube.data.materials.append(cube_material)

# Create and generate a grid of cubes
cube_grid = CubeGrid(5, 5, 1.0)
cube_grid.generate_cubes()


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
