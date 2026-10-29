# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_wallpaper_pattern_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create wallpaper pattern in blender python code

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the hexagons
material_hex = bpy.data.materials.new(name='HexagonMaterial')
material_hex.diffuse_color = (0.5, 0.5, 0.5, 1)  # Set to medium gray

# Function to generate a hexagon at a specified position
def generate_hexagon(position):
    bpy.ops.mesh.primitive_circle_add(vertices=6, radius=1, fill_type='NGON', location=position)
    hex_object = bpy.context.object
    hex_object.data.materials.append(material_hex)
    return hex_object

# Create a grid of hexagons
num_rows = 5
num_cols = 5
for r in range(num_rows):
    for c in range(num_cols):
        x_coord = c * 1.5
        y_coord = r * math.sqrt(3)
        if c % 2 == 1:
            y_coord += math.sqrt(3) / 2
        generate_hexagon((x_coord, y_coord, 0))


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
