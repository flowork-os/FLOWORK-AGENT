# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_puzzle_cube_in_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of puzzle cube in code in Blender

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

class CubeBuilder:
    def __init__(self, positions, colors):
        self.positions = positions
        self.colors = colors

    def create_cubes(self):
        for index, position in enumerate(self.positions):
            self.add_cube(position, self.colors[index])

    def add_cube(self, position, color):
        bpy.ops.mesh.primitive_cube_add(size=1, location=position)
        cube = bpy.context.object
        cube.name = color[0]
        material = bpy.data.materials.new(name=color[0])
        material.diffuse_color = color[1]
        cube.data.materials.append(material)

# Define colors
color_list = [
    ('Scarlet', (1, 0, 0, 1)),
    ('Greenery', (0, 1, 0, 1)),
    ('Navy', (0, 0, 1, 1)),
    ('Lemon', (1, 1, 0, 1)),
    ('Aqua', (0, 1, 1, 1)),
    ('Magenta', (1, 0, 1, 1)),
    ('Peach', (1, 0.5, 0, 1)),
    ('Lavender', (0.5, 0, 0.5, 1)),
]

# Define locations for cubes
cube_locations = [
    (0, 0, 0),
    (1, 0, 0),
    (0, 1, 0),
    (0, 0, 1),
    (1, 1, 0),
    (1, 0, 1),
    (0, 1, 1),
    (1, 1, 1)
]

# Create an instance of CubeBuilder and generate cubes
builder = CubeBuilder(cube_locations, color_list)
builder.create_cubes()


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
