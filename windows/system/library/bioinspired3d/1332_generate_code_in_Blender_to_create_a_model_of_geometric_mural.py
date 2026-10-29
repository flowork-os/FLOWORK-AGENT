# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_code_in_Blender_to_create_a_model_of_geometric_mural" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate code in Blender to create a model of geometric mural

import bpy
import math

# Reset Blender scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for shapes
mat_hex = bpy.data.materials.new(name='Hexagon Material')
mat_hex.diffuse_color = (0.1, 0.5, 0.8, 1)
mat_tri = bpy.data.materials.new(name='Triangle Material')
mat_tri.diffuse_color = (0.8, 0.2, 0.2, 1)
mat_rect = bpy.data.materials.new(name='Rectangle Material')
mat_rect.diffuse_color = (0.2, 0.8, 0.2, 1)

# Functions to create shapes
def add_hexagon(loc, size):
    bpy.ops.mesh.primitive_circle_add(vertices=6, radius=size, fill_type='NGON', location=loc)
    obj = bpy.context.object
    obj.data.materials.append(mat_hex)

def add_triangle(loc, size):
    bpy.ops.mesh.primitive_circle_add(vertices=3, radius=size, fill_type='NGON', location=loc)
    obj = bpy.context.object
    obj.data.materials.append(mat_tri)

def add_rectangle(loc, width, height):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    obj = bpy.context.object
    obj.scale = (width, height, 1)
    obj.data.materials.append(mat_rect)

# Create the main hexagon
add_hexagon((0, 0, 0), 2)

# Create surrounding shapes
for i in range(6):
    angle = math.radians(60 * i)
    x = 4 * math.cos(angle)
    y = 4 * math.sin(angle)
    add_hexagon((x, y, 0), 2)

for i in range(6):
    angle = math.radians(60 * i + 30)
    x = 4 * math.cos(angle)
    y = 4 * math.sin(angle)
    add_triangle((x, y, 0), 1.5)

for i in range(6):
    angle = math.radians(60 * i + 15)
    x = 6 * math.cos(angle)
    y = 6 * math.sin(angle)
    add_rectangle((x, y, 0), 1, 2)


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
