# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_script_create_geometric_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender script create geometric pattern

import bpy
import math

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for shapes
hex_material = bpy.data.materials.new(name='Hexagon Material')
hex_material.diffuse_color = (0.2, 0.6, 0.8, 1)
tri_material = bpy.data.materials.new(name='Triangle Material')
tri_material.diffuse_color = (0.8, 0.2, 0.2, 1)

# Function to add a hexagon
def add_hexagon(size, coords):
    bpy.ops.mesh.primitive_circle_add(vertices=6, radius=size, fill_type='NGON', location=coords)
    hex_shape = bpy.context.object
    hex_shape.data.materials.append(hex_material)

# Function to add a triangle
def add_triangle(size, coords):
    bpy.ops.mesh.primitive_circle_add(vertices=3, radius=size, fill_type='NGON', location=coords)
    tri_shape = bpy.context.object
    tri_shape.data.materials.append(tri_material)

# Set sizes
hex_size = 1
tri_size = hex_size * math.sqrt(3) / 2

# Generate the grid pattern
for row in range(-2, 3):
    for col in range(-2, 3):
        x_coord = row * 1.5 * hex_size
        y_coord = col * math.sqrt(3) * hex_size
        if (row + col) % 2 == 0:
            add_hexagon(hex_size, (x_coord, y_coord, 0))
        else:
            add_triangle(tri_size, (x_coord, y_coord, 0))


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
