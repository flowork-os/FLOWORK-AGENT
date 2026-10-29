# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_flower_pattern_using_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create flower pattern using python blender code

import bpy
import math

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the flower
petal_mat = bpy.data.materials.new(name="Petal Material")
petal_mat.diffuse_color = (1, 0, 0, 1)  # Red
center_mat = bpy.data.materials.new(name="Center Material")
center_mat.diffuse_color = (1, 1, 0, 1)  # Yellow

# Function to build a flower at the given coordinates
def build_flower(coords):
    # Create the center piece
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=coords)
    center_piece = bpy.context.object
    center_piece.name = "Center Sphere"
    center_piece.data.materials.append(center_mat)
    
    # Generate petals in a circular pattern
    petal_radius = 0.15
    for i in range(5):
        theta = i * (2 * math.pi / 5)
        petal_x = coords[0] + 0.3 * math.cos(theta)
        petal_y = coords[1] + 0.3 * math.sin(theta)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=petal_radius, location=(petal_x, petal_y, coords[2]))
        petal_piece = bpy.context.object
        petal_piece.name = f"Petal {i + 1}"
        petal_piece.data.materials.append(petal_mat)

# List of positions for flower instances
flower_coords = [(0, 0, 0), (1, 1, 0), (-1, -1, 0), (1, -1, 0), (-1, 1, 0)]
for flower_loc in flower_coords:
    build_flower(flower_loc)


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
