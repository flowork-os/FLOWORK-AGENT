# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_code_in_Blender_that_creates_a_model_of_floral_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write code in Blender that creates a model of floral pattern.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

flower_color = bpy.data.materials.new(name='Red Flower')
flower_color.diffuse_color = (1, 0, 0, 1)  # Red
base_color = bpy.data.materials.new(name='Gray Surface')
base_color.diffuse_color = (0.8, 0.8, 0.8, 1)  # Light gray

class Flower:
    def __init__(self, position):
        self.position = position
        self.create_flower()

    def create_flower(self):
        x, y, z = self.position
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=self.position)
        center = bpy.context.object
        center.name = 'Flower Center'
        center.data.materials.append(flower_color)
        
        petals = 5
        radius = 0.3
        for i in range(petals):
            angle = i * (2 * math.pi / petals)
            petal_x = x + radius * math.cos(angle)
            petal_y = y + radius * math.sin(angle)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(petal_x, petal_y, z))
            petal = bpy.context.object
            petal.name = f'Petal {i + 1}'
            petal.data.materials.append(flower_color)

bpy.ops.mesh.primitive_cylinder_add(radius=2, depth=0.1, location=(0, 0, 0))
surface = bpy.context.object
surface.name = 'Surface'
surface.data.materials.append(base_color)

flower_coords = [(-1, -1, 0.05), (1, -1, 0.05), (-1, 1, 0.05), (1, 1, 0.05), (0, 0, 0.05)]
for coords in flower_coords:
    Flower(coords)


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
