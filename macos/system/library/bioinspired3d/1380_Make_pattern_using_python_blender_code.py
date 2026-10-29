# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_pattern_using_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make pattern using python blender code

import bpy

# Remove existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize material with a defined color
mat = bpy.data.materials.new(name='NeutralColor')
mat.diffuse_color = (0.4, 0.4, 0.4, 1)  # Darker gray color

# Class to handle the creation of the cube grid
class CubeGrid:
    def __init__(self, size, spacing):
        self.size = size
        self.spacing = spacing

    def build(self):
        for x in range(-self.size, self.size + 1):
            for y in range(-self.size, self.size + 1):
                bpy.ops.mesh.primitive_cube_add(size=0.5, location=(x * self.spacing, y * self.spacing, 0))
                cube = bpy.context.object
                cube.data.materials.append(mat)

# Create the cube grid
grid = CubeGrid(2, 1)
grid.build()


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
