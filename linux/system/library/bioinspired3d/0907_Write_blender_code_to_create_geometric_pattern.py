# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_code_to_create_geometric_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender code to create geometric pattern.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the triangles
triangle_material = bpy.data.materials.new(name='Triangle Material')
triangle_material.diffuse_color = (0.2, 0.8, 0.2, 1)  # Green color

# Function to create a triangle at a given position

def create_triangle(x, y):
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=1, depth=0.1, location=(x, y, 0))
    triangle = bpy.context.object
    triangle.name = f'Triangle_{x}_{y}'
    triangle.data.materials.append(triangle_material)

# Generate a grid of triangles
num_of_triangles = 10
for row in range(num_of_triangles):
    for col in range(num_of_triangles):
        create_triangle(row, col)


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
