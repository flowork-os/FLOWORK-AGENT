# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_python_code_make_modular_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender python code make modular sofa

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Sofa color definition
brown_color = bpy.data.materials.new(name='BrownSofa')
brown_color.diffuse_color = (0.6, 0.4, 0.3, 1)  # Different shade of brown

# Class to handle sofa creation
class Sofa:
    def __init__(self):
        self.material = brown_color

    def add_cube(self, name, location, scale):
        bpy.ops.mesh.primitive_cube_add(size=2, location=location)
        cube = bpy.context.object
        cube.name = name
        cube.scale = scale
        cube.data.materials.append(self.material)

# Instantiate sofa and create components
sofa = Sofa()
sofa.add_cube('Base', (0, 0, 0.5), (1.5, 0.75, 0.25))
sofa.add_cube('Backrest', (0, -0.75, 1.25), (1.5, 0.1, 0.75))

# Create armrests using a loop
for i in range(2):
    x_position = 1.5 * (i * 2 - 1)
    sofa.add_cube(f'Armrest_{i + 1}', (x_position, 0, 0.75), (0.1, 0.75, 0.5))


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
