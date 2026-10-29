# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_python_blender_code_to_create_puzzle_cube" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate python blender code to create puzzle cube

import bpy

# Clear existing meshes from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Color palette
color_palette = [
    (1, 0, 0, 1),  # Bright Red
    (0, 1, 0, 1),  # Vivid Green
    (0, 0, 1, 1),  # Deep Blue
    (1, 1, 0, 1),  # Luminous Yellow
    (1, 0.5, 0, 1),  # Radiant Orange
    (1, 1, 1, 1)   # Pure White
]

# Function to create a cube with a material
def create_colored_cube(position, color):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    cube = bpy.context.object
    cube.name = f'Cube_{position}'
    material = bpy.data.materials.new(name=f'Material_{position}')
    material.diffuse_color = color
    cube.data.materials.append(material)

# Create a 3x3x3 grid of cubes
spacing = 1.1
for x in range(3):
    for y in range(3):
        for z in range(3):
            pos = (x * spacing, y * spacing, z * spacing)
            color = color_palette[(x + y + z) % len(color_palette)]
            create_colored_cube(pos, color)


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
