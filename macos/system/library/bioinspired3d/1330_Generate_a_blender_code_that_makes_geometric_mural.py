# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_blender_code_that_makes_geometric_mural" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a blender code that makes geometric mural

import bpy
import math

# Clear the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for shapes
light_blue_material = bpy.data.materials.new(name='Light Blue Hexagon')
light_blue_material.diffuse_color = (0.1, 0.5, 0.8, 1)
red_material = bpy.data.materials.new(name='Red Triangle')
red_material.diffuse_color = (0.8, 0.2, 0.2, 1)
green_material = bpy.data.materials.new(name='Green Rectangle')
green_material.diffuse_color = (0.2, 0.8, 0.2, 1)

# Function to generate a hexagonal shape

def generate_hexagon(pos, scale):
    bpy.ops.mesh.primitive_circle_add(vertices=6, radius=scale, fill_type='NGON', location=pos)
    hexagon_object = bpy.context.object
    hexagon_object.data.materials.append(light_blue_material)

# Function to generate a triangular shape

def generate_triangle(pos, scale):
    bpy.ops.mesh.primitive_circle_add(vertices=3, radius=scale, fill_type='NGON', location=pos)
    triangle_object = bpy.context.object
    triangle_object.data.materials.append(red_material)

# Function to generate a rectangular shape

def generate_rectangle(pos, width, height):
    bpy.ops.mesh.primitive_plane_add(size=1, location=pos)
    rectangle_object = bpy.context.object
    rectangle_object.scale = (width, height, 1)
    rectangle_object.data.materials.append(green_material)

# Create the central hexagon
generate_hexagon((0, 0, 0), 2)

# Generate surrounding shapes
for index in range(6):
    angle_rad = math.radians(60 * index)
    x_position = 4 * math.cos(angle_rad)
    y_position = 4 * math.sin(angle_rad)
    generate_hexagon((x_position, y_position, 0), 2)

for index in range(6):
    angle_rad = math.radians(60 * index + 30)
    x_position = 4 * math.cos(angle_rad)
    y_position = 4 * math.sin(angle_rad)
    generate_triangle((x_position, y_position, 0), 1.5)

for index in range(6):
    angle_rad = math.radians(60 * index + 15)
    x_position = 6 * math.cos(angle_rad)
    y_position = 6 * math.sin(angle_rad)
    generate_rectangle((x_position, y_position, 0), 1, 2)


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
