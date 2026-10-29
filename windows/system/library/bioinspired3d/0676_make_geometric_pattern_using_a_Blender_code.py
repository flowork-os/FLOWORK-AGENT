# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_geometric_pattern_using_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make geometric pattern using a Blender code

import bpy
import math

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions
light_blue_material = bpy.data.materials.new(name='Light Blue Material')
light_blue_material.diffuse_color = (0.2, 0.6, 0.8, 1)
red_material = bpy.data.materials.new(name='Red Material')
red_material.diffuse_color = (0.8, 0.2, 0.2, 1)

# Helper function to generate a hexagon
def generate_hexagon(radius, position):
    bpy.ops.mesh.primitive_circle_add(vertices=6, radius=radius, fill_type='NGON', location=position)
    hexagon_object = bpy.context.object
    hexagon_object.data.materials.append(light_blue_material)
    return hexagon_object

# Helper function to generate a triangle
def generate_triangle(radius, position):
    bpy.ops.mesh.primitive_circle_add(vertices=3, radius=radius, fill_type='NGON', location=position)
    triangle_object = bpy.context.object
    triangle_object.data.materials.append(red_material)
    return triangle_object

# Define radii
hexagon_radius = 1
triangle_radius = hexagon_radius * math.sqrt(3) / 2

# Create hexagons and triangles in a grid pattern
for x_index in range(-2, 3):
    for y_index in range(-2, 3):
        x_position = x_index * 1.5 * hexagon_radius
        y_position = y_index * math.sqrt(3) * hexagon_radius
        if (x_index + y_index) % 2 == 0:
            generate_hexagon(hexagon_radius, (x_position, y_position, 0))
        else:
            generate_triangle(triangle_radius, (x_position, y_position, 0))


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
