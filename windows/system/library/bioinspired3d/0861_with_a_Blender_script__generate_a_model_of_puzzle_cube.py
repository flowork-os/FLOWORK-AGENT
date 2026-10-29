# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_Blender_script__generate_a_model_of_puzzle_cube" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a Blender script, generate a model of puzzle cube

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Array of colors for the cubes
cube_colors = [
    (1, 0, 0, 1),  # Red
    (0, 1, 0, 1),  # Green
    (0, 0, 1, 1),  # Blue
    (1, 1, 0, 1),  # Yellow
    (1, 0.5, 0, 1),  # Orange
    (1, 1, 1, 1)   # White
]

# Function to generate cubes in a grid

def generate_cubes():
    size = 0.95
    gap = 0.05
    for x in range(3):
        for y in range(3):
            for z in range(3):
                position = (x * (size + gap), y * (size + gap), z * (size + gap))
                bpy.ops.mesh.primitive_cube_add(size=size, location=position)
                cube = bpy.context.object
                cube.name = f"Cube_{x}_{y}_{z}"
                material = bpy.data.materials.new(name=f"Material_{x}_{y}_{z}")
                material.diffuse_color = cube_colors[(x + y + z) % len(cube_colors)]
                cube.data.materials.append(material)

# Call the function to create cubes
generate_cubes()


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
