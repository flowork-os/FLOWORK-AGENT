# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_creates_geometric_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that creates geometric pattern.

import bpy
import math

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the shapes
hex_color = bpy.data.materials.new(name='Hexagon Color')
hex_color.diffuse_color = (0.2, 0.6, 0.8, 1)
tri_color = bpy.data.materials.new(name='Triangle Color')
tri_color.diffuse_color = (0.8, 0.2, 0.2, 1)

# Define a class for shape creation
class ShapeCreator:
    @staticmethod
    def create_hexagon(radius, loc):
        bpy.ops.mesh.primitive_circle_add(vertices=6, radius=radius, fill_type='NGON', location=loc)
        hex_object = bpy.context.object
        hex_object.data.materials.append(hex_color)

    @staticmethod
    def create_triangle(radius, loc):
        bpy.ops.mesh.primitive_circle_add(vertices=3, radius=radius, fill_type='NGON', location=loc)
        tri_object = bpy.context.object
        tri_object.data.materials.append(tri_color)

# Set the radii
hex_radius = 1
tri_radius = hex_radius * math.sqrt(3) / 2

# Create the geometry pattern
for i in range(-2, 3):
    for j in range(-2, 3):
        x_pos = i * 1.5 * hex_radius
        y_pos = j * math.sqrt(3) * hex_radius
        if (i + j) % 2 == 0:
            ShapeCreator.create_hexagon(hex_radius, (x_pos, y_pos, 0))
        else:
            ShapeCreator.create_triangle(tri_radius, (x_pos, y_pos, 0))


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
