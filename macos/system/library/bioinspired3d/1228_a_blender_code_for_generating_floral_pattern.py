# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_for_generating_floral_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code for generating floral pattern

import bpy
import math

# Remove existing mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for flower components
flower_petal = bpy.data.materials.new(name='Flower Petal')
flower_petal.diffuse_color = (1, 0.5, 0.5, 1)

flower_center = bpy.data.materials.new(name='Flower Center')
flower_center.diffuse_color = (1, 1, 0, 1)

# Class to represent a flower
class Flower:
    def __init__(self, position):
        self.position = position
        self.create_flower()

    def create_flower(self):
        for i in range(5):
            angle = i * (2 * math.pi / 5)
            x = 0.2 * math.cos(angle)
            y = 0.2 * math.sin(angle)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(self.position[0] + x, self.position[1] + y, self.position[2]))
            petal = bpy.context.object
            petal.data.materials.append(flower_petal)
        
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=self.position)
        center = bpy.context.object
        center.data.materials.append(flower_center)

# Create a grid of flowers
for row in range(5):
    for col in range(5):
        Flower((row, col, 0))


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
