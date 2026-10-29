# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_that_creates_a_model_of_puzzle_cube" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code that creates a model of puzzle cube

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to generate a cube with a specific color

def generate_colored_cube(position, name, rgba):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    cube = bpy.context.object
    cube.name = name
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = rgba
    cube.data.materials.append(material)

# Color definitions
palette = [
    ('Crimson', (1, 0, 0, 1)),
    ('Lime', (0, 1, 0, 1)),
    ('Azure', (0, 0, 1, 1)),
    ('Gold', (1, 1, 0, 1)),
    ('Turquoise', (0, 1, 1, 1)),
    ('Fuchsia', (1, 0, 1, 1)),
    ('Tangerine', (1, 0.5, 0, 1)),
    ('Violet', (0.5, 0, 0.5, 1)),
]

# Define positions for cube placement
positions = [
    (0, 0, 0),
    (1, 0, 0),
    (0, 1, 0),
    (0, 0, 1),
    (1, 1, 0),
    (1, 0, 1),
    (0, 1, 1),
    (1, 1, 1)
]

# Create the cubes in the specified positions
for index, pos in enumerate(positions):
    color_name, color_rgba = palette[index]
    generate_colored_cube(pos, color_name, color_rgba)


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
