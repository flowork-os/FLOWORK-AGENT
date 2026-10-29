# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_Blender_Python_script_that_creates_geometric_mural" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write Blender Python script that creates geometric mural.

import bpy
import math

# Clean the scene of existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for shapes
hex_color = bpy.data.materials.new(name='Hexagon')
hex_color.diffuse_color = (0.1, 0.5, 0.8, 1)
tri_color = bpy.data.materials.new(name='Triangle')
tri_color.diffuse_color = (0.8, 0.2, 0.2, 1)
rect_color = bpy.data.materials.new(name='Rectangle')
rect_color.diffuse_color = (0.2, 0.8, 0.2, 1)

# Class to create geometric shapes
class ShapeCreator:
    @staticmethod
    def hexagon(location, size):
        bpy.ops.mesh.primitive_circle_add(vertices=6, radius=size, fill_type='NGON', location=location)
        bpy.context.object.data.materials.append(hex_color)

    @staticmethod
    def triangle(location, size):
        bpy.ops.mesh.primitive_circle_add(vertices=3, radius=size, fill_type='NGON', location=location)
        bpy.context.object.data.materials.append(tri_color)

    @staticmethod
    def rectangle(location, width, height):
        bpy.ops.mesh.primitive_plane_add(size=1, location=location)
        rect = bpy.context.object
        rect.scale = (width, height, 1)
        rect.data.materials.append(rect_color)

# Create central hexagon
ShapeCreator.hexagon((0, 0, 0), 2)

# Create surrounding shapes
for i in range(6):
    theta = math.radians(60 * i)
    x_coord = 4 * math.cos(theta)
    y_coord = 4 * math.sin(theta)
    ShapeCreator.hexagon((x_coord, y_coord, 0), 2)

for i in range(6):
    theta = math.radians(60 * i + 30)
    x_coord = 4 * math.cos(theta)
    y_coord = 4 * math.sin(theta)
    ShapeCreator.triangle((x_coord, y_coord, 0), 1.5)

for i in range(6):
    theta = math.radians(60 * i + 15)
    x_coord = 6 * math.cos(theta)
    y_coord = 6 * math.sin(theta)
    ShapeCreator.rectangle((x_coord, y_coord, 0), 1, 2)


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
